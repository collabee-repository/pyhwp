# -*- coding: utf-8 -*-
#
#                   GNU AFFERO GENERAL PUBLIC LICENSE
#                      Version 3, 19 November 2007
#
#   pyhwp : hwp file format parser in python
#   Copyright (C) 2010 mete0r@sarangbang.or.kr
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

def create_service(name, *args):
    import unokit.contexts
    context = unokit.contexts.get_current()
    sm = context.ServiceManager
    if len(args) > 0:
        return sm.createInstanceWithArgumentsAndContext(name, args, context)
    else:
        return sm.createInstanceWithContext(name, context)


class NamespaceNode(object):
    def __init__(self, dotted_name):
        self.dotted_name = dotted_name

    def __getattr__(self, name):
        return NamespaceNode(self.dotted_name + '.' + name)

    def __call__(self, *args):
        return create_service(self.dotted_name, *args)

    def __iter__(self):
        import unokit.contexts
        context = unokit.contexts.get_current()
        sm = context.ServiceManager
        prefix = self.dotted_name + '.'
        for name in sm.AvailableServiceNames:
            if name.startswith(prefix):
                basename = name[len(prefix):]
                if basename.find('.') == -1:
                    yield basename


css = NamespaceNode('com.sun.star')
