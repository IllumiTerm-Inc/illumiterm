# Copyright 2023 Elijah Gordon (NitrixXero) <nitrixxero@gmail.com>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

SUBDIRS = src
ACLOCAL_AMFLAGS = -I m4
DISTCLEANFILES = ChangeLog

dist_doc_DATA = README.md
doc_DATA = ChangeLog

.PHONY: ChangeLog

ChangeLog:
	@if [ -d "$(top_srcdir)/.git" ]; then \
		prev=$$(git describe --tags --always --match '[0-9]*' 2> /dev/null) ; \
		for tag in $$(git tag | egrep '^[0-9]+(\.[0-9]+){1,}' | sort -rV); do \
			if [ x"$$prev" = x ]; then prev=$$tag ; fi ; \
			if [ x"$$prev" = x"$$tag" ]; then continue; fi ; \
			echo "$$prev [ $$(git log $$prev -1 --pretty=format:'%ai') ]:" ; \
			echo "" ; \
			git log --pretty=' - [%h] %s (%an)' $$tag..$$prev ; \
			echo "" ; \
			prev=$$tag ; \
		done > $@ ; \
	else \
		touch $@ ; \
	fi 
