ENV DOCKERHUB_USER fernandosanchez
ENV DOCKERHUB_REPO appstudio
ENV BASEIMAGE node694

FROM ${DOCKERHUB_USER}/${DOCKERHUB_REPO}:${BASEIMAGE}
COPY . /opt/app
ENV APPDIR=opt/app
ENTRYPOINT /opt/node/bin/node /opt/app/bin/www

