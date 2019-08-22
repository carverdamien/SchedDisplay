FROM python:3
WORKDIR /home/server
COPY pip3.install.txt .
RUN pip3 install -r pip3.install.txt
COPY smv smv
COPY *.py ./
ENTRYPOINT ["./server.py"]
EXPOSE 5006
ENV BOKEH_ALLOW_WS_ORIGIN *
