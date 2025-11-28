# Use imagem oficial do Python 3.10
FROM python:3.10-slim

# Cria diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta padrão
EXPOSE 8000

# Comando para iniciar o app
CMD ["gunicorn", "app:app"]
