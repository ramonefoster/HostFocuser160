<h2>OPD Focuser Controller 160</h2>
<p>O controlador do Focalizador implementa um conjunto de manipuladores de comandos. Os comandos possíveis incluem HOME, HALT, CONNECT, DISCONNECT e STATUS. Além disso, a aplicação lida com comandos MOVE e SPEED com parâmetros específicos.<p>

## Comandos Suportados

<b>HOME:</b> Move para o fim de curso de inicialização e zera encoder.\
<b>CONNECT:</b> Basicamente faz uma requisição de status ao se conectar.\
<b>STATUS:</b> Publica o status atual.\
<b>MOVE:</b> Move o valor do foco para uma posição especificada (microns).\
Exemplo: MOVE=posição\
<b>FOCUSIN:</b> Move o valor do foco para dentro com velocidade (microns/s) como parâmetro.\
Exemplo: FOCUSIN=velocidade\
<b>FOCUSOUT:</b> Move o valor do foco para fora com velocidade (microns/s) como parâmetro.\
Exemplo: FOCUSOUT=velocidade\
<b>HALT:</b> Interrompe o Focuser (condicional com base no ID do cliente).

## Utilização

Os clientes devem enviar comandos no seguinte formato JSON:\
<b>{</b>\
    &emsp;<b>"clientId":</b> 1234,\
    &emsp;<b>"clientTransactionId":</b> 9876,\
    &emsp;<b>"clientName":</b> "S4GUI",\
    &emsp;<b>"controller":</b> "Focuser160",\
    &emsp;<b>"action":</b> "NOME_DO_COMANDO"\
<b>}</b>

Substitua <b>NOME_DO_COMANDO</b> pelo comando desejado e forneça parâmetros adicionais conforme necessário. <b>NOME_DO_COMANDO</b> deve ser todo maiúsculo.
<h3>Do Alpaca:</h3> 
<p><b>clientId:</b> Client's unique ID. (1 to 4294967295). The client should choose a value at start-up, e.g. a random value between 1 and 65535, and send this on every transaction to associate entries in device logs with this particular client. Zero is a reserved value that clients should not use.</p>
<b>clientTransactionId:</b> Client's transaction ID. (1 to 4294967295). The client should start this count at 1 and increment by one on each successive transaction. This will aid associating <p>entries in device logs with corresponding entries in client side logs. Zero is a reserved value that clients should not use.</p>

## Resposta do Servidor - Status do Focuser
<p>Ao enviar uma solicitação ao controlador, a resposta contém uma STRING que pode ser convertida para um objeto <b>JSON</b> com informações atualizadas sobre o estado do dispositivo. Aqui está a descrição de cada campo presente na resposta:<p>

<b>absolute: BOOL</b> Indica se o Focalizador está configurado para movimento absoluto (arquivo Config).\
<b>alarm: BOOL</b> Flag de alarme atual.\
<b>cmd: STRING</b> Comando atual ou última ação executada.\
<b>connected: BOOL</b> Indica se o Focalizador está conectado.\
<b>controller: STRING</b> Identifica o HOST (ex: S4GUI).\
<b>device: STRING</b> Identifica o dispositivo que ele aciona (?ex: Mirror2).\
<b>error: STRING</b> Mensagem de erro ou descrição vazia se não houver erro.\
<b>homing: BOOL</b> Indica se o Focalizador está atualmente em processo de homing.\
<b>initialized: BOOL</b> Indica se rotina INIT foi realizada.\
<b>isMoving: BOOL</b> Indica se está atualmente em movimento.\
<b>maxSpeed: INT</b> Velocidade máxima do Focalizador em microns/s (arquivo Config).\
<b>maxStep: INT</b> Número máximo de passos permitidos (arquivo Config).\
<b>tempComp: BOOL</b> Compensação de temperatura (arquivo Config).\
<b>tempCompAvailable: BOOL</b> Indica se a compensação de temperatura está disponível (origem arquivo Config).\
<b>temperature: DOUBLE</b> temperatura do dispositivo (futura implementação).\
<b>timestamp: DOUBLE</b> Data/hora da resposta em formato de timestamp.\
<b>position: DOUBLE</b> Posição atual do Focalizador em mícrons.
