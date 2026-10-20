# Aulão do ENEM — quiz de sala

Jogo de revisão com 11 questões de História, Filosofia e Sociologia, com visual para projetor/TV e alternativas A–E.

## Usar na sala de aula (notebook local)

O notebook hospeda a partida na rede local, sem depender de internet depois da instalação. A versão local tem dois modos: Tablets (cada aluno entra com nome e idade) e Plaquinhas + TV. Os dados ficam em `kahoot.sqlite3` no notebook.

1. Instale Python 3 e execute `py -3 -m pip install -r requirements.txt`.
2. Inicie com `Iniciar-Kahoot.bat` e mantenha a janela aberta.
3. No notebook, acesse `http://localhost:5055/professor` e use o PIN mostrado no terminal.
4. Conecte a TV e os tablets à mesma rede Wi-Fi do notebook. Use o endereço local mostrado no painel; a TV abre `/tv`.
5. Se o Firewall bloquear a rede local, execute `Permitir-Kahoot-Rede-Local.ps1` como Administrador. A regra se limita à sub-rede local. Remova-a depois com `Remover-Regra-Kahoot.ps1`.

Para uma aula sem interrupção, prefira esta execução local: mantenha o notebook conectado à energia e à rede, e desative a suspensão. Faça um teste com os dispositivos antes da aula. Redes escolares podem bloquear comunicação entre dispositivos; o ponto de acesso do notebook é uma alternativa sem internet.

## Demo pública gratuita

Este repositório inclui `render.yaml` para publicar uma demonstração no Render. Ela roda em **Plaquinhas + TV** e bloqueia inscrições, nomes, idades e respostas de alunos; assim, dados de estudantes não são enviados à hospedagem pública. O PIN do professor é gerado pela hospedagem.

Para criar o serviço: conecte este repositório no Render como Blueprint e aplique `render.yaml`. A publicação só termina quando o Render conclui o primeiro deploy e mostra a URL pública.

A hospedagem gratuita pode suspender o serviço após inatividade e reiniciá-lo. O banco configurado fica em armazenamento temporário; o estado de jogo pode ser apagado nesses reinícios. Portanto, a URL pública serve para demonstração/compartilhamento, não como servidor confiável para conduzir uma aula. Para a aula, use o modo local acima.

## Segurança e dados

O painel do professor exige PIN. Na versão local, `professor.pin` e `kahoot.sqlite3` são arquivos privados e estão excluídos do Git. Na demo pública, os endpoints de cadastro são bloqueados. Nunca publique o banco local, o arquivo de PIN ou dados dos estudantes.

## Recursos do painel do professor

O painel acompanha a turma automaticamente, permite buscar participantes por nome, baixar um CSV com pontuação e acertos, copiar o link de acesso da sala e abrir a tela da TV em outra aba. Atalhos de teclado: **N** abre a próxima pergunta, **R** revela a resposta no modo de plaquinhas e **Esc** encerra a pergunta no modo tablets.
