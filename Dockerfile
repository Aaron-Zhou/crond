FROM openshift/base-centos7

MAINTAINER Mateus Caruccio <mateus.caruccio@getupcloud.com>

ENV CRON_VERSION=1.0 \
    HOME=/opt/app-root/src

LABEL io.k8s.description="Crond image" \
      io.k8s.display-name="Cron 1.0" \
      io.openshift.tags="cron,cron1"

RUN yum install -y --enablerepo=centosplus epel-release && \
    INSTALL_PKGS="cronie crontabs nss_wrapper uid_wrapper PyYAML python-requests python-dateutil" && \
    yum install -y --setopt=tsflags=nodocs --enablerepo=centosplus $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum clean all -y

# Allow cron as user
RUN chmod 777 /var/spool/cron/ /var/run/ && \
    chmod u-s /usr/bin/crontab /bin/crontab && \
    chmod u+s /usr/sbin/crond /lib64/libnss_wrapper.so* /lib64/libuid_wrapper.so* && \
    sed -i -s 's/^\(account\s\+include\s\+password-auth\)$/#\1/' /etc/pam.d/crond && \
    sed -i -s 's/^\(session\s\+required\s\+pam_loginuid.so\)$/#\1/' /etc/pam.d/crond && \
    echo -e 'user\ndefault' > /etc/cron.allow && rm -f /etc/cron.deny && \
    mkdir -p /etc/cron/{minutely,hourly,daily,weekly,monthly} && \
    chmod -R g+rw /etc && \
    chmod -R 777 /var/log && \
    fix-permissions $HOME

ADD root /

USER 1001

CMD run-crond
