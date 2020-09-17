# Copyright (c) 2017-2018,2020 - Adjacent Link LLC, Bridgewater,
# New Jersey
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
# * Neither the name of Adjacent Link LLC nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# See toplevel COPYING for more information.

from __future__ import absolute_import, division, print_function

import sys
import os
import re
import traceback
import shutil
from collections import namedtuple, defaultdict
from pkg_resources import resource_filename
from mako.template import Template
from .safe_parser import create_safe_parser
from letce2.utils.filesystem import mkdir_p

try:
    import ConfigParser as configparser
except:
    import configparser

class NodeFilter(object):
    def __init__(self,
                 include_filters,
                 exclude_filters,
                 include_file,
                 exclude_file):
        self._include_filters = include_filters
        self._exclude_filters = exclude_filters
        self._include_set = set()
        self._exclude_set = set()

        if include_file != None:
            for entry in open(include_file,'r'):
                node = entry.strip()
                if node:
                    self._include_set.add(node)

        if exclude_file != None:
            for entry in open(exclude_file,'r'):
                node = entry.strip()
                if node:
                    self._exclude_set.add(node)

    def include_node(self,node_name):
        include = False

        if self._include_filters != None or self._include_set:
            if self._include_filters != None:
                for include_filter in self._include_filters:
                    if re.match(include_filter,node_name):
                        include = True
                        break

            if self._include_set:
                if node_name in self._include_set:
                    include = True
        else:
            include = True

        if self._exclude_filters != None or self._exclude_set:
            if self._exclude_filters != None:
                for exclude_filter in self._exclude_filters:
                    if re.match(exclude_filter,node_name):
                        include = False
                        break

            if self._exclude_set:
                if node_name in self._exclude_set:
                    include = False

        return include

def build_configuration(experiment_configurations,
                        include_filters,
                        exclude_filters,
                        include_file,
                        exclude_file,
                        manifest_file_name,
                        plugin_module_name):

    def get_uses_items(section):
        items = {}
        info = sections[section]

        if info.uses != None:
            items = get_uses_items(info.uses)

        for option in raw_config.options(info.fullname):
            items[option] = raw_config.get(info.fullname,option)

        return items

    def evaluate_configuration(value):
         m = re.match(r'^(.*)@eval{(.+)}(.*)$',value)

         if m:
             result = evaluate_configuration(m.group(2))

             return m.group(1) + result + m.group(3)
         else:
             return eval(value,{})

    def load_node_configuration(node,share):
        local_templates = {}
        local_variables = {}
        local_template_paths = []

        try:
            configuration = {}

            for item,value in safe_config.items(sections[node].fullname):
                m = re.match(r'^(.*)@eval{(.+)}(.*)$',value)

                if m:
                    value =  evaluate_configuration(value)

                configuration[item] = value

        except configparser.InterpolationMissingOptionError as exp:
            print('error loading %s configuration' % node, file=sys.stderr)
            print(exp, file=sys.stderr)
            exit(1)

        for item,value in list(configuration.items()):

            if item == '__template.path':
                local_template_paths = value.split(':')

            elif item.startswith('__template'):
                m = re.match(r'__template\.file\.(\d+)',item)

                if m:
                    if m.group(1):
                        local_templates[m.group(1)] = value
                else:
                    print('ignoring malformed template:',item, file=sys.stderr)

            elif item.count('@') == 1:
                m = re.match(r'(.*?)@(.+)',item)

                if m:
                    targets = m.group(1).split(',')
                    for target in targets:
                        target = target.strip()

                        if target == '+':
                            share[node][m.group(2).strip()] = value
                            target = ''

                        if target not in local_variables:
                            local_variables[target] = {}

                        local_variables[target][m.group(2).strip()] = value

            else:
                print('ignoring malformed configuration:',item, file=sys.stderr)

        return (local_templates,
                local_variables,
                local_template_paths)

    def template_lookup(template,paths,plugin_module):
        search_paths = list(paths)
        search_paths.append('.')
        for path in search_paths:
            target = os.path.join(path,template)

            if os.path.isfile(target):
                if target[0] == '.':
                    target = os.path.join(os.getcwd(),target)
                return target

        # did not find template
        if plugin_module:
            try:
                return resource_filename(plugin_module,
                                         'templates/%s' % template)
            except:
                pass

        raise IOError("template not found: " + template)

    def template_kwargs(template,node,**kwargs):
        kwargs['__node_name'] = node
        kwargs['__top_dir'] = os.getcwd()

        # add variables that are for all templates
        if node in variables:
            if '' in  variables[node]:
                for key,value in list(variables[node][''].items()):
                    kwargs[key] = value

            # add vairables that are for this template
            if template in variables[node]:
                for key,value in list(variables[node][template].items()):
                    kwargs[key] = value

        return kwargs

    # safe config with interpolation
    safe_config = create_safe_parser()

    # raw config without interpolation
    raw_config = configparser.RawConfigParser()

    try:
        files = raw_config.read(experiment_configurations)

        if len(files) != len(experiment_configurations):
            print('error:  unable to open %s' % \
                  ','.join(list(set(experiment_configurations).difference(set(files)))), file=sys.stderr)

        safe_config.read(experiment_configurations)
    except:
        print('error: unable to open',experiment_configurations, file=sys.stderr)
        print(traceback.format_exc())
        exit(1)

    sections = {}

    SectionInfo = namedtuple('SectionInfo',['base','uses','fullname'])

    for section in raw_config.sections():
        m = re.match(r'(!)?([^:]+)(:(.+))?',section)
        if m:
            sections[m.group(2)] = SectionInfo(base=m.group(1) != None,
                                               uses=m.group(4),
                                               fullname=section)

    for section,info in list(sections.items()):
        if info.uses != None:
            for key,value in list(get_uses_items(section).items()):
                safe_config.set(info.fullname,key,value)

    nodes = []
    templates = {}
    variables = {}
    template_paths = {}
    share = defaultdict(dict)
    node_index = {}

    node_filter = NodeFilter(include_filters,
                             exclude_filters,
                             include_file,
                             exclude_file)

    # process container specific config
    for section,info in list(sections.items()):
        if info.base or not node_filter.include_node(section):
            continue

        try:
            os.mkdir(section)
        except:
            pass

        (templates[section],
         variables[section],
         template_paths[section]) = load_node_configuration(section,
                                                            share)

        nodes.append(section)

    # create individual node files
    index = 1
    for node in nodes:
        if node != 'host':
            # build node templates
            for template in list(templates[node].values()):
                target=''

                m = re.match(r'^(.*)@mv{(.+)}$',template)

                if m:
                    template = m.group(1)
                    target = m.group(2)

                template_file = template_lookup(template,template_paths[node],plugin_module_name)

                mako_template = Template(filename=template_file,
                                         future_imports=['absolute_import',
                                                         'division',
                                                         'print_function'])

                kwargs = template_kwargs(template,
                                         node,
                                         __node_index=index)

                out_dir = os.path.join(node,os.path.dirname(target))

                out_file = os.path.basename(target)

                if out_file == '':
                    out_file = template

                if not os.path.isdir(out_dir):
                    mkdir_p(out_dir)

                ofd = open(os.path.join(out_dir,out_file),'w')

                ofd.write(mako_template.render(**kwargs))

                ofd.close()

                os.chmod(os.path.join(out_dir,out_file),
                         os.stat(template_file).st_mode)

            node_index[node] = index

            index += 1

    if 'host' in nodes:
        # build host templates
        for template in list(templates['host'].values()):
            target=''

            m = re.match(r'^(.*)@mv{(.+)}$',template)

            if m:
                template = m.group(1)
                target = m.group(2)

            template_file = template_lookup(template,template_paths['host'],plugin_module_name)

            mako_template = Template(filename=template_file,
                                     future_imports=['absolute_import',
                                                     'division',
                                                     'print_function'])

            kwargs = template_kwargs(template,
                                     'host',
                                     __node_index=node_index,
                                     __share=share)

            out_dir = os.path.join('host',os.path.dirname(target))

            out_file = os.path.basename(target)

            if out_file == '':
                out_file = template

            if not os.path.isdir(out_dir):
                mkdir_p(out_dir)

            ofd = open(os.path.join(out_dir,out_file),'w')

            ofd.write(mako_template.render(**kwargs))

            ofd.close()

            os.chmod(os.path.join(out_dir,out_file),
                     os.stat(template_file).st_mode)


    # create manifest
    ofd = open(manifest_file_name,'w')

    for node in nodes:
        print(node,file=ofd)

    ofd.close()

    return nodes

def nodes_from_manifest(include_filters,
                        exclude_filters,
                        include_file,
                        exclude_file,
                        manifest_file_name):
    nodes_include = []
    nodes_exclude = []

    node_filter = NodeFilter(include_filters,
                             exclude_filters,
                             include_file,
                             exclude_file)

    if os.path.isfile(manifest_file_name):
        for entry in open(manifest_file_name,'r'):
            node = entry.strip()
            if node_filter.include_node(entry):
                nodes_include.append(node)
            else:
                nodes_exclude.append(node)

    return (nodes_include,nodes_exclude)

def nodes_to_manifest(nodes,
                      manifest_file_name):
    # create manifest
    ofd = open(manifest_file_name,'w')

    for node in nodes:
        print(node,file=ofd)

    ofd.close()

def clean_configuration(nodes,
                        manifest_file_name):
    if nodes:
        for node in nodes:
            if os.path.isdir(node):
                shutil.rmtree(node)

        os.remove(manifest_file_name)
