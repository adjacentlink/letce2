FROM centos:centos7

RUN mkdir -p /opt/built

RUN yum -y install epel-release
RUN yum -y update

# Copy and install packages from the latest upsteam dependencies
WORKDIR /opt
RUN mkdir -p dependencies
# RUN yum -y install dependencies/*\.rpm

# Build tools
RUN yum -y install git gcc-c++ make autoconf automake libtool rpm-build

RUN git clone https://github.com/adjacentlink/letce2 -b develop
WORKDIR letce2
RUN ./autogen.sh
RUN ./configure --with-python2
RUN make rpm
RUN cp $(find .rpmbuild/RPMS -name "*\.rpm") /opt/built
RUN yum -y install /opt/built/*

RUN yum clean all

RUN echo 'complete'

