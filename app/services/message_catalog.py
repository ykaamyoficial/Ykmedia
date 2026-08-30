from app.core.config import settings
from app.models.interactive import InteractivePrompt

_TYPE_LABELS = {
    "video": "vídeo",
    "imagem": "imagem",
    "audio": "áudio",
    "documento": "documento",
    "link": "link",
    "desconhecida": "arquivo",
}

_TEAM = "equipe de Sonoplastia"


class WhatsAppMessageCatalog:
    FOOTER = "YkMedia"

    COMMAND_DESCRIPTIONS = {
        "ajuda": "Mostra esta ajuda.",
        "status": "Diz em que passo você parou.",
        "recomeçar": "Reinicia a conversa.",
        "cancelar": "Cancela a conversa e descarta os arquivos.",
    }

    # ----- rótulos de botões / listas -----

    @classmethod
    def category_prompt(cls) -> str:
        return "Toque para escolher a categoria."

    @classmethod
    def category_button_text(cls) -> str:
        return "Ver categorias"

    @classmethod
    def options_button_text(cls) -> str:
        return "Ver opções"

    @classmethod
    def filename_prompt(cls) -> str:
        return "Como devo nomear este arquivo?"

    @classmethod
    def keep_original_title(cls) -> str:
        return "Manter o nome original"

    @classmethod
    def custom_filename_title(cls) -> str:
        return "Escolher um novo nome"

    @classmethod
    def auto_number_title(cls) -> str:
        return "Numerar automaticamente"

    @classmethod
    def one_by_one_title(cls) -> str:
        return "Nomear um por um"

    @classmethod
    def next_page_title(cls) -> str:
        return "Ver mais"

    @classmethod
    def previous_page_title(cls) -> str:
        return "Voltar"

    @classmethod
    def help_prompt(cls) -> str:
        return "Como posso ajudar?"

    @classmethod
    def status_title(cls) -> str:
        return "Ver status"

    @classmethod
    def restart_title(cls) -> str:
        return "Recomeçar"

    @classmethod
    def cancel_title(cls) -> str:
        return "Cancelar"

    @classmethod
    def confirm_title(cls) -> str:
        return "Confirmar envio"

    @classmethod
    def correct_title(cls) -> str:
        return "Corrigir"

    @classmethod
    def collect_done_title(cls) -> str:
        return "Concluir envio"

    # ----- coleta de arquivos -----

    @classmethod
    def collecting_step(
        cls,
        summary: str,
        contact_name: str | None = None,
        nudge: bool = False,
    ) -> str:
        if nudge:
            return (
                "Ainda não terminou? Pode enviar mais arquivos, ou toque em "
                "*Concluir envio* quando estiver pronto."
            )
        saudacao = f"Olá, {contact_name}! 👋" if contact_name else "Olá! 👋"
        return (
            f"{saudacao} Aqui é o assistente da {_TEAM}.\n\n"
            f"{summary} Pode continuar enviando — quando terminar, toque em "
            "*Concluir envio* e eu te ajudo a organizar (categoria, nome e confirmação).\n"
            "_(para sair, envie *cancelar*)_"
        )

    # ----- passo 1: categoria -----

    @classmethod
    def category_step(
        cls,
        summary: str,
        menu_text: str,
        contact_name: str | None = None,
        invalid: bool = False,
    ) -> str:
        options = cls.numbered_options_from_text(menu_text)
        if invalid:
            lead = "Não encontrei essa opção. Escolha uma da lista abaixo. 👇"
        else:
            saudacao = f"Olá, {contact_name}! 👋" if contact_name else "Olá! 👋"
            lead = (
                f"{saudacao} Aqui é o assistente da {_TEAM}.\n\n"
                "Vou te ajudar a organizar seus arquivos em *3 passos rápidos*: "
                "categoria, nome e confirmação.\n"
                "_(para sair a qualquer momento, envie *cancelar*)_"
            )

        return (
            f"{lead}\n\n"
            f"*Passo 1 de 3 · Categoria*\n\n"
            f"{summary} Em qual categoria devo organizá-{cls._los(summary)}?\n\n"
            f"{options}"
        )

    # ----- passo 2: nome -----

    @classmethod
    def filename_decision_text(cls, total: int = 1) -> str:
        if total > 1:
            return (
                "*Passo 2 de 3 · Nomes*\n\n"
                f"São *{total} arquivos*. Como devo nomeá-los?\n"
                f"1️⃣ {cls.auto_number_title()} (01, 02, 03…)\n"
                f"2️⃣ {cls.one_by_one_title()}"
            )
        return (
            "*Passo 2 de 3 · Nome*\n\n"
            f"{cls.filename_prompt()}\n"
            f"1️⃣ {cls.keep_original_title()}\n"
            f"2️⃣ {cls.custom_filename_title()}"
        )

    @classmethod
    def custom_filename_request(
        cls,
        index: int | None = None,
        total: int | None = None,
    ) -> str:
        if index is not None and total is not None:
            return (
                f"*Arquivo {index} de {total}* — que nome devo dar?\n"
                "_Sem extensão. Ex.: Cartaz Culto Domingo_"
            )
        return (
            "Digite o nome do arquivo, sem extensão.\n"
            "_Ex.: Cartaz Culto Domingo_"
        )

    @classmethod
    def invalid_filename(cls) -> str:
        return 'Esse nome não pode ser usado (evite / \\ : * ? " < > |). Envie outro, por favor.'

    @classmethod
    def invalid_filename_decision(cls, prompt: InteractivePrompt) -> str:
        return "Não entendi. Responda com *1* para manter o nome ou *2* para escolher um novo."

    # ----- passo 3: confirmação -----

    @classmethod
    def confirmation_step(
        cls,
        category: str | None,
        filename: str | None,
        count: int = 1,
        batch_filenames: tuple[str, ...] = (),
    ) -> str:
        from app.services.conversation_engine import KEEP_ORIGINAL_FILENAME

        if count > 1 and batch_filenames:
            lista = "\n".join(f"   {index}. {name}" for index, name in enumerate(batch_filenames, 1))
            arquivos = f"📄 Arquivos ({count}):\n{lista}"
        elif count > 1:
            arquivos = f"📄 Arquivos: {count} (numerados automaticamente: 01, 02, 03…)"
        elif not filename or filename == KEEP_ORIGINAL_FILENAME:
            arquivos = "📄 Nome: o nome original do arquivo"
        else:
            arquivos = f"📄 Nome: {filename}"

        return (
            "*Passo 3 de 3 · Confirmação*\n\n"
            "Revise antes de enviar para a equipe:\n\n"
            f"📁 Categoria: *{category or '—'}*\n"
            f"{arquivos}"
        )

    @classmethod
    def invalid_confirmation(cls) -> str:
        return "Não entendi. Toque em *Confirmar envio*, *Corrigir* ou *Cancelar*."

    # ----- encerramento -----

    @classmethod
    def media_finished(
        cls,
        contact_name: str | None = None,
        category: str | None = None,
        count: int = 1,
    ) -> str:
        greeting = f"✅ Pronto, {contact_name}!" if contact_name else "✅ Pronto!"
        arquivos = "1 arquivo" if count <= 1 else f"{count} arquivos"
        salvos = "salvo" if count <= 1 else "salvos"
        onde = f" em *{category}*" if category else ""
        return (
            f"{greeting} *{arquivos}* {salvos}{onde}.\n\n"
            f"A {_TEAM} já tem acesso. Obrigado! 🙌\n\n"
            "_Precisa enviar mais? É só mandar o próximo arquivo._"
        )

    @classmethod
    def conversation_finished(cls) -> str:
        return "Envie um arquivo quando precisar organizar mais alguma coisa."

    @classmethod
    def link_processing(cls) -> str:
        return (
            "Recebi seu link e estou baixando o vídeo — isso pode levar alguns minutos. ⏳\n\n"
            "Assim que terminar, eu te chamo para escolher a categoria."
        )

    @classmethod
    def expiry_warning(cls) -> str:
        return (
            "Ainda está aí? Sua conversa expira em *5 minutos*. "
            "Envie qualquer mensagem para continuar de onde parou."
        )

    @classmethod
    def conversation_timeout(cls) -> str:
        return (
            "Sua conversa expirou por inatividade — *nenhum arquivo foi enviado* para a equipe.\n\n"
            "Quando puder, reenvie os arquivos e a gente recomeça. Sem problema. 🙂"
        )

    # ----- fora de conversa -----

    @classmethod
    def usage_info(cls) -> str:
        return (
            f"Olá! Aqui é o canal de mídias da {_TEAM}. 🎛️\n\n"
            "📎 *Para enviar mídias do culto:* mande os arquivos ou um link (YouTube) "
            "por aqui e eu te guio em 3 passos.\n"
            "💬 *Outro assunto:* pode escrever à vontade — a equipe responde assim que possível."
        )

    # ----- resumos -----

    @classmethod
    def media_summary(cls, total: int, type_counts: dict[str, int]) -> str:
        if total <= 1:
            return "Recebi *1 arquivo*."

        parts = []
        for key, count in type_counts.items():
            label = _TYPE_LABELS.get(key, key)
            if count > 1:
                label = f"{label}s" if not label.endswith("s") else label
            parts.append(f"{count} {label}")
        detalhe = f" ({cls._join_natural(parts)})" if parts else ""
        return f"Recebi *{total} arquivos*{detalhe}."

    # ----- comandos -----

    @classmethod
    def commands_unavailable(cls) -> str:
        return "Os comandos estão indisponíveis no momento."

    @classmethod
    def command_help(cls) -> str:
        lines = [
            f"• *{command}* — {description}"
            for command, description in cls.COMMAND_DESCRIPTIONS.items()
        ]
        return (
            f"Sou o assistente de mídias da {_TEAM}. Envie um arquivo ou link e "
            "eu organizo em 3 passos.\n\n" + "\n".join(lines)
        )

    @classmethod
    def command_cancelled(cls) -> str:
        return (
            "Conversa cancelada e arquivos descartados. "
            "Quando quiser recomeçar, é só enviar um arquivo. 🙂"
        )

    @classmethod
    def command_no_active_conversation(cls) -> str:
        return "Você não tem nenhuma conversa em andamento. Envie um arquivo para começar."

    @classmethod
    def command_status(cls, state: str) -> str:
        return f"Você está no passo: {cls._friendly_state(state)}."

    @classmethod
    def command_restarted(cls) -> str:
        return "Conversa reiniciada. Pode enviar os arquivos de novo."

    @classmethod
    def command_version(cls) -> str:
        return f"YkMedia {settings.APP_VERSION}"

    @classmethod
    def command_unknown(cls) -> str:
        return "Não reconheci esse comando. Envie *ajuda* para ver o que eu faço."

    @classmethod
    def pending_file_missing_finish(cls) -> str:
        return (
            "Não encontrei o arquivo para finalizar. Pode reenviá-lo, por favor?"
        )

    # ----- utilitários -----

    @classmethod
    def menu_text(cls, prompt: InteractivePrompt) -> str:
        options = cls._numbered(prompt)
        if not options:
            return prompt.text
        return f"{prompt.text}\n\n{options}" if prompt.text else options

    @classmethod
    def numbered_options_from_text(cls, menu_text: str) -> str:
        # menu_text pode vir como "<texto>\n\n<lista>"; guardamos só a lista.
        if "\n\n" in menu_text:
            return menu_text.split("\n\n", 1)[1]
        return menu_text

    @classmethod
    def _numbered(cls, prompt: InteractivePrompt) -> str:
        return "\n".join(
            f"{index} - {option.title}"
            for index, option in enumerate(prompt.options, start=1)
            if not option.id.startswith("action:next_page")
            and not option.id.startswith("action:previous_page")
        )

    @staticmethod
    def _los(summary: str) -> str:
        return "los" if "arquivos" in summary else "lo"

    @staticmethod
    def _join_natural(parts: list[str]) -> str:
        if len(parts) <= 1:
            return "".join(parts)
        return f"{', '.join(parts[:-1])} e {parts[-1]}"

    @staticmethod
    def _friendly_state(state: str) -> str:
        return {
            "AGUARDANDO_MIDIA": "recebendo os arquivos",
            "AGUARDANDO_CATEGORIA": "escolha da categoria",
            "AGUARDANDO_RENOMEAR": "escolha do nome",
            "AGUARDANDO_NOME_ARQUIVO": "digitação do nome",
            "AGUARDANDO_CONFIRMACAO": "confirmação",
            "FINALIZADO": "concluído",
        }.get(state, state)
