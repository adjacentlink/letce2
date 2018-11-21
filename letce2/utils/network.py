# Copyright (c) 2018 - Adjacent Link LLC, Bridgewater, New Jersey
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

import socket
import struct

class CIDRNotation(object):
    @staticmethod
    def split(cidr_notation):
        index = cidr_notation.find('/')
        if index == -1:
            return(cidr_notation,None)
        else:
            return (cidr_notation[:index],int(cidr_notation[index+1:]))

    @staticmethod
    def netmask(cidr_notation):
        address,prefix_length = CIDRNotation.split(cidr_notation)

        mask = 0

        if prefix_length:
            for i in range(0,prefix_length):
                mask += 1 << 32 - (i + 1)

        if not mask:
            raise ValueError('bad CIDR notation: {}'.format(cidr_notation))

        return socket.inet_ntoa(struct.pack('!L',mask))


    @staticmethod
    def network(cidr_notation,with_prefix_length=False):
        address,prefix_length = CIDRNotation.split(cidr_notation)

        mask = 0

        if prefix_length:
            for i in range(0,prefix_length):
                mask += 1 << 32 - (i + 1)

        if not mask:
            raise ValueError('bad CIDR notation: {}'.format(cidr_notation))

        try:
            address=struct.unpack('!L',socket.inet_aton(address))[0]
        except Exception as exp:
            raise exp

        if with_prefix_length:
            return '{}/{}'.format(socket.inet_ntoa(struct.pack('!L',mask&address)),
                                  prefix_length)
        else:
            return socket.inet_ntoa(struct.pack('!L',mask&address))

    @staticmethod
    def broadcast(cidr_notation,with_prefix_length=False):
        address,prefix_length = CIDRNotation.split(cidr_notation)

        mask = 0

        if prefix_length:
            for i in range(0,prefix_length):
                mask += 1 << 32 - (i + 1)

        if not mask:
            raise ValueError('bad CIDR notation: {}'.format(cidr_notation))

        try:
            address=struct.unpack('!L',socket.inet_aton(address))[0]
        except Exception as exp:
            raise exp

        mask = ~mask & 0xffffffff

        if with_prefix_length:
            return '{}/{}'.format(socket.inet_ntoa(struct.pack('!L',mask|address)),
                                  prefix_length)
        else:
            return socket.inet_ntoa(struct.pack('!L',mask|address))

    @staticmethod
    def address(cidr_notation):
        return CIDRNotation.split(cidr_notation)[0]


    @staticmethod
    def prefix_length(cidr_notation):
        return CIDRNotation.split(cidr_notation)[1]
