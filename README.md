## Controlador HOST do Focalizador:
<h2>(Client faz comandos PUSH na porta 7002)</h2>
<b>"INIT"</b> realiza a rotina INIT/HOME;
<b>"CONN"</b> estabelece conexão com o motor e informa o client que está conectado;
<b>"PING"</b> envia um comando ping ao motor e informa se está "reachable" ou "unreachable";
<b>"DC"</b> desfaz a conexão;
<b>"HALT"</b> para qualquer movimento;
<b>"M{pos}"</b> (exemplo M1000) movimenta até a posição 1000;
<h2>(Client SUB na porta 7001)</h2>
Recebe um JSON com:
status = {
        "absolute": Config.absolute,
        "maxincrement": Config.maxincrement,
        "tempcomp": Config.temp_comp,
        "tempcompavailable": Config.tempcompavailable,
        "ismoving": False,
        "position": 0,
        "error": '',
        "connected": False,
        "homing": False,
        "athome": False
        }

