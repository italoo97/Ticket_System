# Ticket_System
Ticket System for Discord, with Transcript site

======================= PT-BR =======================

# Sistema de Tickets para Discord

Sistema de tickets desenvolvido por mim para comercialização com clientes donos de cidades de fivem para atendimento a usuarios.

Tecnologias/Bibliotecas Utilizadas:
  - Cogs
  - Flask-API (Flask / Flask_Cors)
  - Banco de Dados DuckDB
  - Discord / Discord.ext / Discord.ui

Arquivo Config:
DB_TICKETS = "tickets.duckdb" (Nome do Banco de Dados)
ARQUIVO_JSON = "tickets.json" (Nome do json para salvar o ID da mensagem para abrir os tickets e manter a persistencia)
ID_DEVOLUCAO =  int (Canal aonde Irá uma Embed com informações para realizar devolução de itens)
CARGOS_SLASH = [int] (Quem irá poder aceitrar as devoluções)
CANAL_TICKET = int (Canal de Solicitação de Abertura de um Ticket)
LOG_TICKET = int (Canal que irá ser enviado a log do ticket so ser fechado)
SUPORTE_ID = int (Categoria de onde o Ticket Ficará aberto)

Fluxo de Funcionamento:

Após Utilizar o comando !setup_tickets no CANAL_TICKET ele irá enviar uma embed com um botão com as opções de tickets que o usuario poderá solicitar, automaticamente o sistema ja salva o ID da mensagem em ARQUIVO_JSON para toda vez que o bot for reiniciado ele manter a persistencia e não precisar mandar novamente o comando !setup_tickets.

Ao clicar em abrir ticket ele abre uma lista com as opções de tickets que podem ser abertos, e ao selecionar uma ele manda uma nova embed efemera com um botão para ir para o ticket.

<img width="588" height="574" alt="image" src="https://github.com/user-attachments/assets/d7885645-07a4-4cbc-9ca2-84b02344cad7" />
<img width="607" height="166" alt="image" src="https://github.com/user-attachments/assets/0cf65968-140b-4ad1-a38e-3595d7620253" />
<img width="491" height="421" alt="image" src="https://github.com/user-attachments/assets/dea117ec-862a-45e3-93b6-8591b65f17c7" />
<img width="579" height="412" alt="image" src="https://github.com/user-attachments/assets/bf1d4d8f-8bdd-4f95-a9c1-014b16fefcc3" />

Para abrir o ticket ele pega as permissoes da categoria e adiciona apenas o criador do ticket para poder enviar mensagem tambem, o nome do canal e gerado aleatoriamente com 6 caracteres podendo eles serem mesclados com numero e letras, e manda uma embed de boas vindas com os botoes de ação para gerenciamento.

<img width="803" height="753" alt="image" src="https://github.com/user-attachments/assets/4b4eb16e-5526-4c43-808e-434c979e585b" />

Botoes:
  - Cancelar Ticket: Somente quem abriu o ticket pode utilizar ele (essa informação e salva no banco de dados), Então caso alguem que foi adicionado queira fexhar ele não consegue.
  - Poke: É enviado uma mensagem no PV de quem criou o ticket com uma mensagem de saudação e informando quem chamou a atenção dele e em qual canal está sendo solicitado uma resposta do mesmo, junto com um atalho e uma marcação do canal para facilitar o acesso ao ticket.
<img width="679" height="105" alt="image" src="https://github.com/user-attachments/assets/f94533b5-4bcf-48b0-a31c-4881e24be509" />
<img width="452" height="289" alt="image" src="https://github.com/user-attachments/assets/b84ff507-8d5f-4023-ac03-28ba9d5868ce" />
  - Ações Ticket: Ele envia uma mensagem efemera com uma lista com as opções de renomear ticket e transferir de categoria.
<img width="567" height="166" alt="image" src="https://github.com/user-attachments/assets/d2852584-8db7-4df0-86a1-a66c597408a8" />
<img width="509" height="206" alt="image" src="https://github.com/user-attachments/assets/91b23bdf-e924-4bf0-b96b-7151ba279258" />
  - Devolução: Abre um Formulario para preencher o ID de quem receberá os itens de volta e os itens a seren devolvidos, apos envio será enviado uma enbed no canal ID_DEVOLUCAO com os botão de aprovar ou negar, ao ter a interação os botão são excluidos e a embed é atualizada com o nome de quem aprovou ou negou, essas informações são salvas na base de dados para manter a persistencia.
<img width="493" height="467" alt="image" src="https://github.com/user-attachments/assets/539b53aa-04a4-45f8-9e80-4039f0f418a4" />
<img width="435" height="105" alt="image" src="https://github.com/user-attachments/assets/3de8572e-ec5b-4f7a-9eaf-22e31f6f9cff" />
<img width="377" height="375" alt="image" src="https://github.com/user-attachments/assets/0f8488b7-2469-4570-80f6-a6b7b12ca4e9" />
<img width="373" height="524" alt="image" src="https://github.com/user-attachments/assets/ab363476-e762-4343-b6c4-e0f4ee2e6ed2" />
  - Adicionar Membro: Caso tenha a necessidade de adicionar outro jogador e só pesquisar o nome dele do discord no canal chat-geral por exemplo e apertar o botão que ele manda a instrução para marcar a pessoa e enviar a mensagem, se em 15 segundos ninguem for marcado ele desativa o monitoramento, caso voce mande a mensagem com quem voce quer adicionar ele informa que o usuario marcado foi adicionado.
<img width="638" height="226" alt="image" src="https://github.com/user-attachments/assets/c08def08-3dc7-45f5-9fdb-6e4f6027d13f" />
<img width="630" height="219" alt="image" src="https://github.com/user-attachments/assets/0a17aae3-69c7-48f4-8b22-5bc63b7a2ace" />
  - Remover Membro: Igual o Adicionar porem so funciona com quem esta no ticket e não tem cargo para visualizar
<img width="632" height="220" alt="image" src="https://github.com/user-attachments/assets/88f64c69-7f30-462c-9831-f9e23d439ac6" />
  - Adicionar Observação: A proxima mensagem que for digitada no chat será salva como uma observação no banco de dados
<img width="543" height="105" alt="image" src="https://github.com/user-attachments/assets/178eb5ff-d272-4fb1-85ee-bf123c16b65e" />
  - Fechar ticket: Somente quem tem um cargo em CARGOS_SLASH pode fechar o ticket, ao clicar ele informa no canal que o ticket foi fechado e em 10 Segundos o canal e excluido, alem disso ele manda uma embed no privado de quem abriu o ticket e uma no LOG_TICKET.
<img width="393" height="66" alt="image" src="https://github.com/user-attachments/assets/71a656f7-2024-4574-ac67-a444123098b0" />
<img width="354" height="269" alt="image" src="https://github.com/user-attachments/assets/cc364f20-79f4-4a3c-a999-f194aee5436b" />
<img width="650" height="408" alt="image" src="https://github.com/user-attachments/assets/70dd5987-6de3-42b1-a394-5bbcc30d9c97" />
  - Assumir Ticket: Quem irá resolver o ticket assume para ele o ticket
<img width="786" height="103" alt="image" src="https://github.com/user-attachments/assets/953bfcb9-431b-4912-8663-a73273fd850d" />
  - Chamada de Voz: Caso seja necessario conversar com alguem sobre o ticket ele cria um canal de voz que se ele ficar 5 minutos sem ninguem ele exclui automaticamente.
<img width="547" height="111" alt="image" src="https://github.com/user-attachments/assets/3301824f-0cc4-4aac-9bc5-9a4c47315d92" />
<img width="221" height="47" alt="image" src="https://github.com/user-attachments/assets/be0d34a5-3871-4f1c-821c-a2267973c6e8" />
 
Gerenciamento apos o fechamento:
   - No LOG_TICKET será enviado o identificador e o token do ticket, o identificador e para achar ele futuramente no servidor e o token para criar a rota do transcript na base de dados, assim como quem fechou, quem abriu e a hora e data que foi aberto, assim como o transcript original.
  - Para ver o ticket em um site foi utilizado a hospedagem da discloud, e a rota para acessar o ticket ficou "/api/ticket/<token>" assim como a rota para conseguir o transcript "SELECT html_content FROM ticket_html WHERE token = ?"
<img width="1298" height="690" alt="image" src="https://github.com/user-attachments/assets/24d75814-782a-4c94-bc6a-f2412797bfe8" />

"https://maliticket.discloud.app/api/ticket/0fea3b83-7922-4854-97a8-bbb2558e265b"

O Arquivo main.py ficou com 111 linhas por conta das logs, ja o cogs\tickets.py ficou com 1686 linhas.






