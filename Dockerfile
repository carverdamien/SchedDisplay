FROM python:3
WORKDIR /home/server
COPY pip3.install.txt .
RUN pip3 install -r pip3.install.txt
COPY smv smv
COPY server.py ./
COPY static ./static
COPY disposable ./disposable
COPY jupyter-notebook.sh ./
COPY entrypoint.sh ./
ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 5006 443
ENV BOKEH_ALLOW_WS_ORIGIN *
