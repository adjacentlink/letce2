# Copyright (c) 2017-2018 - Adjacent Link LLC, Bridgewater, New Jersey
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

try:
    import ConfigParser as configparser
except:
    import configparser

def create_safe_parser():
    if sys.version_info >= (3,3):
        class LETCEInterpolation(configparser.BasicInterpolation):
            def _interpolate_some(self, parser, option, accum, rest, section, map,
                                  depth):
                rawval = parser.get(section, option, raw=True, fallback=rest)
                if depth > configparser.MAX_INTERPOLATION_DEPTH:
                    raise InterpolationDepthError(option, section, rawval)
                while rest:
                    p = rest.find("%")
                    if p < 0:
                        accum.append(rest)
                        return
                    if p > 0:
                        accum.append(rest[:p])
                        rest = rest[p:]
                    # p is no longer used
                    c = rest[1:2]
                    if c == "%":
                        accum.append("%")
                        rest = rest[2:]
                    elif c == "(":
                        m = self._KEYCRE.match(rest)
                        if m is None:
                            raise InterpolationSyntaxError(option, section,
                                "bad interpolation variable reference %r" % rest)
                        var = parser.optionxform(m.group(1))
                        rest = rest[m.end():]
                        try:
                            v = map[var]
                        except KeyError:
                            if var[0] != '+':
                                try:
                                    v = map['+' + var]
                                except:
                                    raise configparser.InterpolationMissingOptionError(
                                        option, section, rest, var)
                            else:
                                raise configparser.InterpolationMissingOptionError(
                                    option, section, rest, var)

                        if "%" in v:
                            self._interpolate_some(parser, option, accum, v,
                                                   section, map, depth + 1)
                        else:
                            accum.append(v)
                    else:
                        raise InterpolationSyntaxError(
                            option, section,
                            "'%%' must be followed by '%%' or '(', "
                            "found: %r" % (rest,))

        return configparser.ConfigParser(interpolation=LETCEInterpolation())
    else:
        class LETCESafeConfigParser(configparser.SafeConfigParser):
            def _interpolate_some(self, option, accum, rest, section, map, depth):
                if depth > configparser.MAX_INTERPOLATION_DEPTH:
                    raise configparser.InterpolationDepthError(option, section, rest)
                while rest:
                    p = rest.find("%")
                    if p < 0:
                        accum.append(rest)
                        return
                    if p > 0:
                        accum.append(rest[:p])
                        rest = rest[p:]
                    # p is no longer used
                    c = rest[1:2]
                    if c == "%":
                        accum.append("%")
                        rest = rest[2:]
                    elif c == "(":
                        m = self._interpvar_re.match(rest)
                        if m is None:
                            raise configparser.InterpolationSyntaxError(option, section,
                                "bad interpolation variable reference %r" % rest)
                        var = self.optionxform(m.group(1))
                        rest = rest[m.end():]
                        try:
                            v = map[var]
                        except KeyError:
                            if var[0] != '+':
                                try:
                                    v = map['+' + var]
                                except:
                                    raise configparser.InterpolationMissingOptionError(
                                        option, section, rest, var)
                            else:
                                raise configparser.InterpolationMissingOptionError(
                                    option, section, rest, var)

                        if "%" in v:
                            self._interpolate_some(option, accum, v,
                                                   section, map, depth + 1)
                        else:
                            accum.append(v)
                    else:
                        raise configparser.InterpolationSyntaxError(
                            option, section,
                            "'%%' must be followed by '%%' or '(', found: %r" % (rest,))


        # safe config with interpolation
        return LETCESafeConfigParser()
