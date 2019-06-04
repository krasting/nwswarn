FROM multiarch/debian-debootstrap:amd64-stretch-slim

ENV PACKAGE=http://www.noaaport.net/software/packages/npemwin-2.4.13p1/packages/debian-9/amd64/npemwin_2.4.13p1-1_amd64.deb

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    dumb-init curl tcl tcllib libwrap0 gnuplot-nox unzip git python3 python3-pip python3-venv vim && \
    wget -O /tmp/npemwin.deb "${PACKAGE}" && \
    dpkg -i /tmp/npemwin.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/npemwin.deb

RUN pip3 install python-dateutil
RUN pip3 install pytz
RUN pip3 install twilio
RUN pip3 install virtualenv

COPY sorted_fips.txt /usr/local/nws-warning/sorted_fips.txt
COPY warning.py /usr/local/nws-warning/warning.py

# Updated EMWIN server list
COPY servers.conf /usr/local/etc/npemwin/servers.conf

# Updated rssfilters.rc file to trigger warning script
COPY rssfilter.rc /usr/local/etc/npemwin/defaults/rssfilter.rc

# Main config file /usr/local/etc/npemwin/npemwind.conf

VOLUME [ "/var/npemwin" ]
VOLUME [ "/usr/local/etc/npemwin" ]
VOLUME [ "/usr/local/libexec/npemwin/" ]

EXPOSE 8016

USER noaaport:noaaport

ENTRYPOINT ["dumb-init", "--"]

CMD ["/usr/local/sbin/npemwind","-D","-D"]

# Metadata from original Dockerfile
ARG VCS_REF="Unknown"
LABEL maintainer="jb@nrgup.net" \
    org.label-schema.name="Docker NPEMWIN" \
    org.label-schema.description="Docker container for NPEMWIN" \
    org.label-schema.url="http://www.noaaport.net/" \
    org.label-schema.vcs-ref="${VCS_REF}" \
    org.label-schema.vcs-url="https://github.com/bradsjm/dockerfiles" \
    org.label-schema.schema-version="1.0"
