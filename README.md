## Gerando novos módulos

O código da import automático nos módulos presentes dentro do diretório ```all_modules/```

Basta adicionar outro diretório ou outro módulo dentro dos diretórios existentes

TODO: conferir se o módulo é "importável". Caso um módulo não seja, vai dar pau

## Usando o Dockerfile

1 - Criar a imagem docker pelo Dockerfile

    docker build -f Dockerfile -t discordmusicbot .

2 - Executar o container

    docker run -it discordmusicbot /bin/bash

3 - Executar o bot

    python discord_bot/bot.py -t

obs: 

A flag ```-t``` é para ambiente de testes. O bot será o ```testeMusiquinha```. O prefixo para ele é ```#```

Para instalar o ```ffmpeg``` precisa dar update na imagem do ubuntu e isso leva tempo. Aconselho dar o build uma vez e 
enviar os arquivos modificados com o ```docker cp```

## Sem o Dockerfile (aconselho um ambiente virtual. Ajuda nos módulos python mas não pro ffmpeg)

1 - Criar o ambiente virtual com python 3.8

    python3.8 -m venv venv-discord

2 - Acessar o ambiente virtual

    source venv-discord/bin/activate

3 - Instalar todas as dependências do ```requirements.txt```

    pip install -r requirements.txt

4 - Instalar o ```ffmpeg```. Necessário para que o áudio das músicas sejam executados.

    apt-get install ffmpeg

5 - Executar o bot

    python discord_bot/bot.py -t