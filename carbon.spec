Summary:	Back-end data caching and persistence daemon for Graphite
Name:		carbon
Version:	0.9.10
Release:	0.1
License:	Apache v2.0
Group:		Daemons
Source0:	https://github.com/downloads/graphite-project/carbon/%{name}-%{version}.tar.gz
# Source0-md5:	053b2df1c928250f59518e9bb9f35ad5
Source1:	%{name}-cache.init
Source2:	%{name}-relay.init
Source3:	%{name}-aggregator.init
Source4:	%{name}.sysconfig
Patch0:		FHS.patch
URL:		https://launchpad.net/graphite/
BuildRequires:	python-devel
BuildRequires:	python-setuptools
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.658
Provides:	group(carbon)
Provides:	user(carbon)
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	python-TwistedCore >= 8.0
Requires:	python-whisper
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define	no_install_post_check_tmpfiles 1

%description
Twisted daemon that listens for time-series data and writes this data
out to whisper databases, relays the data or aggregates the data.
Carbon is a data collection and storage agent.

%prep
%setup -q
%patch0 -p1

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install \
	--skip-build \
	--optimize=2 \
	--root=$RPM_BUILD_ROOT

%py_postclean -x amqp_publisher.py,amqp_listener.py

install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install -d $RPM_BUILD_ROOT%{_localstatedir}/log/carbon
install -d $RPM_BUILD_ROOT%{_localstatedir}/run/carbon
install -d $RPM_BUILD_ROOT%{_sharedstatedir}/carbon

# Install system configuration and init scripts
install -Dp %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/carbon-cache
install -Dp %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/carbon-relay
install -Dp %{SOURCE3} $RPM_BUILD_ROOT/etc/rc.d/init.d/carbon-aggregator
install -Dp %{SOURCE4} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/carbon

# Install default configuration files
install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install -Dp conf/carbon.conf.example $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/carbon.conf
install -Dp conf/storage-schemas.conf.example $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/storage-schemas.conf

# Temp mv to non .py locations
cd $RPM_BUILD_ROOT%{_bindir}
%{__mv} carbon-aggregator.py carbon-aggregator
%{__mv} carbon-cache.py carbon-cache
%{__mv} carbon-client.py carbon-client
%{__mv} carbon-relay.py carbon-relay
%{__mv} validate-storage-schemas.py validate-storage-schemas

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 290 -r carbon
%useradd -u 290 -r -g carbon -d %{_sharedstatedir}/carbon -s /sbin/nologin -c "Carbon cache daemon" carbon

%post
/sbin/chkconfig --add carbon-aggregator
/sbin/chkconfig --add carbon-cache
/sbin/chkconfig --add carbon-relay
%service carbon-aggregator restart
%service carbon-cache restart
%service carbon-relay restart

%preun
if [ $1 -eq 0 ]; then
	/sbin/chkconfig --del carbon-aggregator
	/sbin/chkconfig --del carbon-cache
	/sbin/chkconfig --del carbon-relay
	%service carbon-aggregator stop
	%service carbon-cache stop
	%service carbon-relay stop
fi

%postun
if [ $1 = 0 ]; then
	%userremove carbon
	%groupremove carbon
fi

%files
%defattr(644,root,root,755)
%doc conf/*
%dir %{_sysconfdir}/%{name}
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/carbon.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/storage-schemas.conf
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/carbon
%attr(754,root,root) /etc/rc.d/init.d/carbon-aggregator
%attr(754,root,root) /etc/rc.d/init.d/carbon-cache
%attr(754,root,root) /etc/rc.d/init.d/carbon-relay
%attr(755,root,root) %{_bindir}/carbon-aggregator
%attr(755,root,root) %{_bindir}/carbon-cache
%attr(755,root,root) %{_bindir}/carbon-client
%attr(755,root,root) %{_bindir}/carbon-relay
%attr(755,root,root) %{_bindir}/validate-storage-schemas

%dir %{py_sitescriptdir}/%{name}
%attr(755,root,root) %{py_sitescriptdir}/%{name}/amqp_publisher.py
%attr(755,root,root) %{py_sitescriptdir}/%{name}/amqp_listener.py
%{py_sitescriptdir}/%{name}/*.py[co]
%{py_sitescriptdir}/%{name}/amqp0-8.xml
%dir %{py_sitescriptdir}/%{name}/aggregator
%{py_sitescriptdir}/%{name}/aggregator/*.py[co]
%{py_sitescriptdir}/%{name}-%{version}-py*.egg-info

# FIXME/CHECKME: twisted itself packages /usr/lib64/python2.7/site-packages/twisted/plugins dir
%dir %{py_sitescriptdir}/twisted
%dir %{py_sitescriptdir}/twisted/plugins
%{py_sitescriptdir}/twisted/plugins/carbon_*.py[co]

%dir %{_localstatedir}/run/%{name}
%dir %attr(775,root,carbon) %{_localstatedir}/log/%{name}
%dir %attr(775,root,carbon) %{_sharedstatedir}/%{name}
