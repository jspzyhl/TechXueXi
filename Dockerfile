
FROM python:3.7-slim
ARG usesource="https://github.com/jspzyhl/TechXueXi.git"
ARG usebranche="developing"
ENV pullbranche=${usebranche}
ENV Sourcepath=${usesource}
RUN apt-get update
RUN apt-get install -y wget unzip libzbar0 git cron supervisor
ENV TZ=Asia/Shanghai
ENV AccessToken=
ENV Secret=
ENV Nohead=True
ENV Pushmode=2
ENV islooplogin=False
ENV CRONTIME="30 9 * * *"
ENV AutoLoginHost=
# RUN rm -f /xuexi/config/*; ls -la
COPY requirements.txt /xuexi/requirements.txt
COPY run.sh /xuexi/run.sh 
COPY start.sh /xuexi/start.sh 
COPY supervisor.sh /xuexi/supervisor.sh

RUN apt-get install -y lsb-release gnupg debconf-utils
RUN { \
        echo mysql-apt-config mysql-apt-config/repo-codename select buster ; \
        echo mysql-apt-config mysql-apt-config/repo-distro select debian ; \
        echo mysql-apt-config mysql-apt-config/select-preview select Disabled ; \
        echo mysql-apt-config mysql-apt-config/select-server select mysql-5.7 ; \
        echo mysql-apt-config mysql-apt-config/select-product select Ok ; \
        echo mysql-apt-config mysql-apt-config/repo-url string http://repo.mysql.com/apt ; \
        echo mysql-apt-config mysql-apt-config/select-tools select Disabled ; \
        echo mysql-community-server mysql-community-server/root-pass password 1234 ; \
        echo mysql-community-server mysql-community-server/re-root-pass password 1234 ; \
    } | debconf-set-selections && \
    chmod 777 /root && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 467B942D3A79BD29 && \
    cd /xuexi/ && \
    wget https://dev.mysql.com/get/mysql-apt-config_0.8.18-1_all.deb && \
    export DEBIAN_FRONTEND=noninteractive && \
    dpkg -i mysql-apt-config*.deb && \
    apt-get update && \
    apt install -y mysql-community-server

RUN pip install -r /xuexi/requirements.txt
RUN cd /xuexi/; \
  wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_92.0.4515.159-1_amd64.deb; \
  dpkg -i google-chrome-stable_92.0.4515.159-1_amd64.deb; \
  apt-get -fy install; \
  google-chrome --version; \
  rm -f google-chrome-stable_92.0.4515.159-1_amd64.deb
RUN cd /xuexi/; \
  wget -O chromedriver_linux64_92.0.4515.107.zip http://npm.taobao.org/mirrors/chromedriver/92.0.4515.107/chromedriver_linux64.zip; \
  unzip chromedriver_linux64_92.0.4515.107.zip; \
  chmod 755 chromedriver; \
  ls -la; \
  ./chromedriver --version
RUN apt-get clean
WORKDIR /xuexi
RUN chmod +x ./run.sh
RUN chmod +x ./start.sh
RUN chmod +x ./supervisor.sh;./supervisor.sh
RUN mkdir code
WORKDIR /xuexi/code
RUN git clone -b ${usebranche} ${usesource}; cp -r /xuexi/code/TechXueXi/SourcePackages/* /xuexi;
WORKDIR /xuexi
EXPOSE 80
ENTRYPOINT ["/bin/bash", "./start.sh"]
