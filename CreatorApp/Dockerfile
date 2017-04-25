FROM fernandosanchez/appstudio:node694

COPY . /opt/app
ENV APPDIR=opt/app
ENV MESOS_SANDBOX=/opt/app
ENTRYPOINT /opt/node/bin/node /opt/app/bin/www
