FROM ubuntu:latest
LABEL authors="chipo"

ENTRYPOINT ["top", "-b"]