# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: Exp $

EAPI=3

PYTHON_DEPEND="2"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="3.*"

inherit distutils subversion

ESVN_REPO_URI="http://volti.googlecode.com/svn/trunk/"
ESVN_PROJECT="volti"

DESCRIPTION="GTK+ application for controlling audio volume from system tray/notification area"
HOMEPAGE="http://code.google.com/p/volti/"
SRC_URI=""

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE="libnotify X"

RDEPEND=">=dev-python/pygtk-2.16
	>=dev-python/pyalsaaudio-0.6
	dev-python/dbus-python
	X? ( >=dev-python/python-xlib-0.15_rc1 )
	libnotify? ( x11-libs/libnotify )"
DEPEND=""

S=${WORKDIR}/${PN}

DOCS="AUTHORS ChangeLog README"
