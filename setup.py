#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
gedit-git-plugin
Copyright 2013 Yan-ren Tsai <elleryq@gmail.com>

This file is part of gedit-git-plugin.

gedit-git-plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

gedit-git-plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with gedit-plugin-ipython.  If not, see <http://www.gnu.org/licenses/>.
"""

from distutils.core import setup

setup(name='gedit-git-plugin',
      version='0.1',
      description='Gedit plugin to show git difference',
      author='Yan-ren Tsai',
      author_email='elleryq@gmail.com',
      url='https://github.com/elleryq/gedit-git-plugin',
      scripts=[],
      data_files=[
          ('lib/gedit/plugins', ['git.plugin']),
          ('lib/gedit/plugins/git', ['git/diffrenderer.py',
           'git/__init__.py', 'git/viewactivatable.py']),
      ]
      )
