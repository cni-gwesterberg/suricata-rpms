%define prerelease_tag rc2

Summary: Intrusion Detection System
Name: suricata
Version: 4.1.0
Release: 0.4%{prerelease_tag}%{?dist}
License: GPLv2
Group: Applications/Internet
URL: http://suricata-ids.org/
Source0: https://www.openinfosecfoundation.org/download/%{name}-%{version}-%{prerelease_tag}.tar.gz
Source1: suricata.service
Source2: suricata.sysconfig
Source3: suricata.logrotate
Source4: fedora.notes
Source5: suricata-tmpfiles.conf

# Irrelevant docs are getting installed, drop them
Patch1: suricata-2.0.9-docs.patch
# liblua is not named correctly in epel 7.
Patch2: suricata-2.0.2-lua.patch

BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: libyaml-devel
BuildRequires: libnfnetlink-devel libnetfilter_queue-devel libnet-devel
BuildRequires: zlib-devel libpcap-devel pcre-devel libcap-ng-devel
BuildRequires: nspr-devel nss-devel nss-softokn-devel file-devel
BuildRequires: jansson-devel GeoIP-devel python2-devel lua-devel
BuildRequires: autoconf automake libtool
BuildRequires: systemd
BuildRequires: hiredis-devel
BuildRequires: libevent-devel
BuildRequires: libprelude-devel
BuildRequires: pkgconfig(gnutls)

BuildRequires: gcc-c++
BuildRequires: rust cargo

%if 0%{?fedora} >= 25
%ifarch x86_64
BuildRequires: hyperscan-devel
Requires: ragel
%endif
%endif

%if 0%{?centos} == 7
%ifarch x86_64
BuildRequires: hyperscan-static
BuildRequires: hyperscan-devel
%endif
%endif

Requires(pre): /usr/sbin/useradd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
The Suricata Engine is an Open Source Next Generation Intrusion
Detection and Prevention Engine. This engine is not intended to
just replace or emulate the existing tools in the industry, but
will bring new ideas and technologies to the field. This new Engine
supports Multi-threading, Automatic Protocol Detection (IP, TCP,
UDP, ICMP, HTTP, TLS, FTP and SMB! ), Gzip Decompression, Fast IP
Matching, and GeoIP identification.

%prep
%setup -q -n suricata-%{version}-%{prerelease_tag}
install -m 644 %{SOURCE4} doc/
%patch1 -p1
%if 0%{?rhel} == 7
%patch2 -p1
%endif

autoreconf -fv --install

%build

# Required for Hyperscan on CentOS 7.
%if 0%{?centos} == 7
export LIBS="-lstdc++ -lm -lgcc_s -lgcc -lc -lgcc_s -lgcc"
%endif

%configure --enable-gccprotect --enable-pie --disable-gccmarch-native --disable-coccinelle --enable-nfqueue --enable-af-packet --with-libnspr-includes=/usr/include/nspr4 --with-libnss-includes=/usr/include/nss3 --enable-jansson --enable-geoip --enable-lua --enable-hiredis --enable-prelude

%make_build

%install
make DESTDIR="%{buildroot}" "bindir=%{_sbindir}" install

# Setup etc directory
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/rules
install -m 600 rules/*.rules %{buildroot}%{_sysconfdir}/%{name}/rules
install -m 600 *.config %{buildroot}%{_sysconfdir}/%{name}
install -m 600 suricata.yaml %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m 0755 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}

# Set up logging
mkdir -p %{buildroot}/%{_var}/log/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# Remove a couple things so they don't get picked up
rm -rf %{buildroot}%{_includedir}
rm -f %{buildroot}%{_libdir}/libhtp.la
rm -f %{buildroot}%{_libdir}/libhtp.a
rm -f %{buildroot}%{_libdir}/libhtp.so
rm -rf %{buildroot}%{_libdir}/pkgconfig

# Setup tmpdirs
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 %{SOURCE5} %{buildroot}%{_tmpfilesdir}/%{name}.conf
mkdir -p %{buildroot}/run
install -d -m 0755 %{buildroot}/run/%{name}/

%check
make check

%pre
getent passwd suricata >/dev/null || useradd -r -M -s /sbin/nologin suricata

%post
/sbin/ldconfig
%systemd_post suricata.service

%preun
%systemd_preun suricata.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart suricata.service

%files
%doc doc/Basic_Setup.txt
%doc doc/Setting_up_IPSinline_for_Linux.txt doc/fedora.notes
%{!?_licensedir:%global license %%doc}
%license COPYING
%attr(644,root,root) %{_mandir}/man1/*
%{_sbindir}/suricata
%{_bindir}/suricatasc
%{_bindir}/suricatactl
%{_bindir}/suricata-update
%{_libdir}/libhtp*
%{python2_sitelib}/suricatasc/*
%{python2_sitelib}/suricata/*
%{python2_sitelib}/suricata*.egg-info
%config(noreplace) %attr(-,suricata,-) %{_sysconfdir}/%{name}/suricata.yaml
%config(noreplace) %attr(-,suricata,-) %{_sysconfdir}/%{name}/*.config
%config(noreplace) %attr(-,suricata,-) %{_sysconfdir}/%{name}/rules/*.rules
%config(noreplace) %attr(0600,suricata,root) %{_sysconfdir}/sysconfig/%{name}
%attr(644,root,root) %{_unitdir}/suricata.service
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/logrotate.d/%{name}
%attr(750,suricata,root) %dir %{_var}/log/%{name}
%attr(750,suricata,root) %dir %{_sysconfdir}/%{name}
%attr(750,suricata,root) %dir %{_sysconfdir}/%{name}/rules
%attr(750,suricata,root) %dir /run/%{name}/
%attr(755,root,root) %dir %{_datadir}/%{name}/rules
%attr(644,root,root) %{_datadir}/%{name}/rules/*
%{_tmpfilesdir}/%{name}.conf

%changelog
* Mon Aug 13 2018 Steve Grubb <sgrubb@redhat.com> - 4.0.5-3
- Consolidate branches so that everything is in sync (#1614935)

* Fri Aug 10 2018 Jason Taylor <jtfas90@gmail.com> 4.0.5-2
- fixes bz#1614935

* Wed Jul 18 2018 Jason Taylor <jtfas90@gmail.com> - 4.0.5-1
- upstream security fix release
- addresses CVE-2018-10242, CVE-2018-10243, CVE-2018-10244

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Jul 09 2018 Jason Taylor <jtfas90@gmail.com> - 4.0.4-2
- bumped release for build against hyperscan 5.0.0

* Mon Jul 09 2018 Jason Taylor <jtfas90@gmail.com> - 4.0.4-1
- added gcc-c++ buildrequires

* Thu Feb 15 2018 Jason Taylor <jtfas90@gmail.com> - 4.0.4-1
- fixes bz#1543250 and bz#1543251
- multiple upstream bugfixes

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Mon Dec 11 2017 Jason Taylor <jtfas90@gmail.com> 4.0.3-2
- Added prelude support

* Fri Dec 08 2017 Jason Taylor <jtfas90@gmail.com> 4.0.3-1
- Upstream bugfix release

* Wed Oct 18 2017 Steve Grubb <sgrubb@redhat.com> 4.0.1-1
- Upstream bugfix update

* Tue Sep 26 2017 Steve Grubb <sgrubb@redhat.com> 4.0.0-2
- Make suricata user own /run/suricata (#1396150)

* Mon Jul 31 2017 Jason Taylor <jtfas90@gmail.com> 4.0.0-1
- Latest upstream major release
- Build now has hyperscan and redis support

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 13 2017 Jason Taylor <jtfas90@gmail.com> 3.2.3-1
- Upstream bugfix update

* Wed Jun 07 2017 Steve Grubb <sgrubb@redhat.com> 3.2.2-1
- Upstream bugfix update

* Wed Mar 22 2017 Jason Ish <ish@unx.ca> - 3.2.1-2
- Re-enable PID file due to selinux issues.

* Tue Mar 14 2017 Jason Ish <ish@unx.ca> - 3.2.1-2
- Use systemctl instead of a PID file for log rotation.

* Wed Feb 15 2017 Steve Grubb <sgrubb@redhat.com> 3.2.1-1
- Upstream security update

* Mon Feb 13 2017 Steve Grubb <sgrubb@redhat.com> 3.2-1
- New upstream feature release
- Rotate /var/log/suricata/eve.json (#1396151)
- Fix ownership of /run/suricata (#1396150)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Nov 01 2016 Steve Grubb <sgrubb@redhat.com> 3.1.3-1
- New upstream bug fix release

* Wed Oct  5 2016 Jason Ish <ish@unx.ca> - 3.1.2-2
- Fix ownership of /var/suricata.

* Wed Sep 07 2016 Steve Grubb <sgrubb@redhat.com> 3.1.2-1
- New upstream bug fix release

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.1-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed Jul 13 2016 Steve Grubb <sgrubb@redhat.com> 3.1.1-1
- New upstream bug fix release

* Wed Jun 22 2016 Steve Grubb <sgrubb@redhat.com> 3.1-1
- New upstream bug fix release

* Mon Apr 04 2016 Steve Grubb <sgrubb@redhat.com> 3.0.1-1
- New upstream bug fix release

* Wed Mar 16 2016 Steve Grubb <sgrubb@redhat.com> 3.0-2
- Fixed Bug 1227085 - Have Suricata start after the network is online

* Mon Mar 07 2016 Steve Grubb <sgrubb@redhat.com> 3.0-1
- New upstream bug fix release

* Wed Feb 10 2016 Peter Schiffer <pschiffe@redhat.com> 2.0.11-3
- Run suricata under suricata user

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Dec 28 2015 Steve Grubb <sgrubb@redhat.com> 2.0.11-1
- New upstream bug fix release

* Wed Nov 25 2015 Steve Grubb <sgrubb@redhat.com> 2.0.10-1
- New upstream bug fix release

* Sat Oct 03 2015 Steve Grubb <sgrubb@redhat.com> 2.0.9-1
- New upstream bug fix release

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed May 06 2015 Steve Grubb <sgrubb@redhat.com> 2.0.8-1
- New upstream security bug fix release

* Thu Feb 26 2015 Steve Grubb <sgrubb@redhat.com> 2.0.7-1
- New upstream security bug fix release for CVE-2015-0928

* Thu Jan 15 2015 Steve Grubb <sgrubb@redhat.com> 2.0.6-1
- New upstream bug fix release
- Don't use the system libhtp library

* Fri Dec 12 2014 Steve Grubb <sgrubb@redhat.com> 2.0.5-1
- New upstream bug fix release
- Use the system libhtp library

* Tue Oct 28 2014 Jason Ish <ish@unx.ca> - 2.0.4-1
- Use SIGHUP for log rotation instead of copytruncate.

* Wed Sep 24 2014 Steve Grubb <sgrubb@redhat.com> 2.0.4-1
- New upstream bug fix release
- Fixes CVE-2014-6603 out-of-bounds access in SSH parser

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug 08 2014 Steve Grubb <sgrubb@redhat.com> 2.0.3-1
- New upstream bug fix release

* Sat Jun 28 2014 Steve Grubb <sgrubb@redhat.com> 2.0.2-2
- Specfile cleanups (#1113413)

* Wed Jun 25 2014 Steve Grubb <sgrubb@redhat.com> 2.0.2-1
- New upstream bug fix release
- Enable liblua support

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Steve Grubb <sgrubb@redhat.com> 2.0.1-1
- New upstream bug fix release

* Wed Mar 26 2014 Steve Grubb <sgrubb@redhat.com> 2.0-1
- Major new upstream release with new features

* Tue Jan 21 2014 Dan Horák <dan[at]danny.cz> 1.4.7-3
- luajit available only on selected arches

* Sat Jan 11 2014 Steve Grubb <sgrubb@redhat.com> 1.4.7-2
- Enable luajit support

* Wed Dec 18 2013 Steve Grubb <sgrubb@redhat.com> 1.4.7-1
- New upstream bug fix release

* Fri Oct 04 2013 Steve Grubb <sgrubb@redhat.com> 1.4.6-1
- New upstream bug fix release

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jun 21 2013 Steve Grubb <sgrubb@redhat.com> 1.4.3-2
- Drop prelude support

* Fri Jun 21 2013 Steve Grubb <sgrubb@redhat.com> 1.4.3-1
- New upstream bug fix release

* Mon Jun 03 2013 Steve Grubb <sgrubb@redhat.com> 1.4.2-1
- New upstream bug fix release

* Sun Mar 10 2013 Steve Grubb <sgrubb@redhat.com> 1.4.1-1
- New upstream bugfix release
- Enable libgeoip support
- Switch to stack-protector-all

* Fri Feb 15 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 20 2012 Steve Grubb <sgrubb@redhat.com> 1.4-1
- New upstream feature enhancement release

* Thu Dec 06 2012 Steve Grubb <sgrubb@redhat.com> 1.3.5-1
- New upstream bugfix release

* Tue Nov 27 2012 Steve Grubb <sgrubb@redhat.com> 1.3.4-1
- New upstream release

* Mon Nov 05 2012 Steve Grubb <sgrubb@redhat.com> 1.3.3-1
- New upstream release

* Tue Oct 09 2012 Steve Grubb <sgrubb@redhat.com> 1.3.2-2
- Add nss-devel build require and systemd macros

* Mon Oct 08 2012 Steve Grubb <sgrubb@redhat.com> 1.3.2-1
- New upstream release

* Sat Aug 25 2012 Steve Grubb <sgrubb@redhat.com> 1.3.1-1
- New upstream release
- Switch startup to use systemd

* Fri Jul 06 2012 Steve Grubb <sgrubb@redhat.com> 1.3-1
- New upstream release

* Fri Mar 30 2012 Jon Ciesla <limburgher@gmail.com> - 1.2.1-3
- Rebuild for updated libnet.

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 1.2.1-2
- Rebuild against PCRE 8.30

* Thu Feb 02 2012 Steve Grubb <sgrubb@redhat.com> 1.2.1-1
- New upstream release

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Dec 22 2011 Steve Grubb <sgrubb@redhat.com> 1.1.1-2
- Enable AF_PACKET support

* Wed Dec 07 2011 Steve Grubb <sgrubb@redhat.com> 1.1.1-1
- New upstream release

* Mon Jul 25 2011 Steve Grubb <sgrubb@redhat.com> 1.0.5-1
- New upstream release

* Fri Jun 24 2011 Steve Grubb <sgrubb@redhat.com> 1.0.4-1
- New upstream release

* Thu Apr 28 2011 Dan Horák <dan[at]danny.cz> 1.0.3-2
- don't override -march set by the buildsystem (fixes build on non-x86)

* Sat Apr 23 2011 Steve Grubb <sgrubb@redhat.com> 1.0.3-1
- New upstream release

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Nov 10 2010 Steve Grubb <sgrubb@redhat.com> 1.0.2-1
- New upstream release (#651978)

* Thu Jul 01 2010 Steve Grubb <sgrubb@redhat.com> 1.0.0-1
- New upstream release

* Fri May 07 2010 Steve Grubb <sgrubb@redhat.com> 0.9.0-1
- New upstream release

* Tue Apr 20 2010 Steve Grubb <sgrubb@redhat.com> 0.8.2-1
- New upstream release

* Sat Feb 27 2010 Steve Grubb <sgrubb@redhat.com> 0.8.1-1
- Initial packaging

