# extrator-fatura-itau
Já quis extrair as transações do seu cartão Itaú em formato CSV e se frustou miseravelmente? Este repositório quer te ajudar.


## Como executar

### 1. Instale as dependências
```sh
pip install -r requirements.txt
```

### 2. Mova os pdfs para a pasta `input`

### 3. Execute o programa
```sh
python main.py 
```

### 4. O arquivo CSV será salvo na pasta `output` como `ouput.csv`


### Ou utilize o docker

### 1. Mova os pdfs para a pasta `input`

### 2. Execute
```sh
docker compose --file docker-compose.yml up app --build
```

### 3. O arquivo CSV será salvo na pasta `output` como `ouput.csv`