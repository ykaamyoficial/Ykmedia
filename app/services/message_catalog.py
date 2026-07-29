from app.core.config import settings
from app.models.interactive import InteractivePrompt


class WhatsAppMessageCatalog:
    FOOTER = "YkMedia"

    COMMAND_DESCRIPTIONS = {
        "!ajuda": "Lista os comandos.",
        "!cancelar": "Cancela a conversa.",
        "!status": "Mostra o status da conversa.",
        "!reiniciar": "Reinicia a conversa.",
        "!versao": "Mostra a versao.",
    }

    @classmethod
    def category_prompt(cls) -> str:
        return "Escolha a categoria em que deseja organizar seus arquivos."

    @classmethod
    def category_button_text(cls) -> str:
        return "Categorias"

    @classmethod
    def options_button_text(cls) -> str:
        return "Opcoes"

    @classmethod
    def filename_prompt(cls) -> str:
        return "Deseja renomear este arquivo?"

    @classmethod
    def keep_original_title(cls) -> str:
        return "Manter nome"

    @classmethod
    def custom_filename_title(cls) -> str:
        return "Informar nome"

    @classmethod
    def next_page_title(cls) -> str:
        return "Proximas"

    @classmethod
    def previous_page_title(cls) -> str:
        return "Anteriores"

    @classmethod
    def help_prompt(cls) -> str:
        return "Como posso ajudar?"

    @classmethod
    def status_title(cls) -> str:
        return "Ver status"

    @classmethod
    def restart_title(cls) -> str:
        return "Reiniciar"

    @classmethod
    def cancel_title(cls) -> str:
        return "Cancelar"

    @classmethod
    def custom_filename_request(cls) -> str:
        return "Digite o nome do arquivo, sem extensao."

    @classmethod
    def invalid_category(cls, prompt: InteractivePrompt) -> str:
        return cls._with_prefix("Opcao invalida.", cls.menu_text(prompt))

    @classmethod
    def invalid_filename_decision(cls, prompt: InteractivePrompt) -> str:
        return cls._with_prefix("Opcao invalida.", cls.menu_text(prompt))

    @classmethod
    def invalid_filename(cls) -> str:
        return "Nome invalido. Envie outro nome."

    @classmethod
    def media_finished(cls) -> str:
        return "Seus arquivos foram organizados com sucesso.\n\nObrigado!"

    @classmethod
    def conversation_finished(cls) -> str:
        return "Envie outro arquivo quando precisar."

    @classmethod
    def media_session_started(cls, summary: str, menu_text: str) -> str:
        return f"{summary}\n\n{menu_text}"

    @classmethod
    def usage_info(cls) -> str:
        return (
            "Ola! Esta e uma resposta automatica da equipe de Sonoplastia.\n\n"
            "Para enviar midias para a programacao do culto, envie seus arquivos ou um link compativel "
            "e responda ao questionario.\n\n"
            "Se for outro assunto, basta enviar sua mensagem. Assim que possivel nossa equipe fara o atendimento."
        )

    @classmethod
    def filename_decision_text(cls) -> str:
        return (
            f"{cls.filename_prompt()}\n\n"
            f"1 - {cls.keep_original_title()}\n"
            f"2 - {cls.custom_filename_title()}"
        )

    @classmethod
    def media_batch_updated(cls, summary: str) -> str:
        return f"{summary}\n\nContinue enviando arquivos ou escolha a categoria quando terminar."

    @classmethod
    def media_summary(cls, total: int, type_counts: dict[str, int]) -> str:
        if total <= 1:
            return "Recebi 1 arquivo."

        labels = {
            "video": "video",
            "imagem": "imagem",
            "audio": "audio",
            "documento": "documento",
            "link": "link",
            "desconhecida": "arquivo",
        }
        lines = [f"Recebi {total} arquivos.", "Resumo:"]
        for key, count in type_counts.items():
            label = labels.get(key, key)
            plural = "s" if count > 1 else ""
            lines.append(f"- {count} {label}{plural}")
        return "\n".join(lines)

    @classmethod
    def conversation_timeout(cls) -> str:
        return (
            "Nao recebemos sua resposta dentro do tempo esperado.\n\n"
            "Por seguranca, seus arquivos nao foram enviados para a Sonoplastia.\n"
            "Caso ainda deseje envia-los, basta reenviar os arquivos e responder ao questionario."
        )

    @classmethod
    def pending_file_missing_start(cls) -> str:
        return "Nao encontrei o arquivo. Envie novamente."

    @classmethod
    def pending_file_missing_finish(cls) -> str:
        return "Nao encontrei o arquivo para finalizar. Envie novamente."

    @classmethod
    def commands_unavailable(cls) -> str:
        return "Comandos indisponiveis agora."

    @classmethod
    def command_help(cls) -> str:
        lines = [
            f"{command} - {description}"
            for command, description in cls.COMMAND_DESCRIPTIONS.items()
        ]
        return "Comandos:\n" + "\n".join(lines)

    @classmethod
    def command_cancelled(cls) -> str:
        return "Conversa cancelada."

    @classmethod
    def command_no_active_conversation(cls) -> str:
        return "Nao ha conversa ativa."

    @classmethod
    def command_status(cls, state: str) -> str:
        return f"Status da conversa: {state}."

    @classmethod
    def command_restarted(cls) -> str:
        return "Conversa reiniciada."

    @classmethod
    def command_version(cls) -> str:
        return f"YkMedia {settings.APP_VERSION}"

    @classmethod
    def command_unknown(cls) -> str:
        return "Comando nao reconhecido. Envie !ajuda."

    @classmethod
    def menu_text(cls, prompt: InteractivePrompt) -> str:
        options = "\n".join(
            f"{index} - {option.title}"
            for index, option in enumerate(prompt.options, start=1)
            if not option.id.startswith("action:next_page")
            and not option.id.startswith("action:previous_page")
        )
        if not options:
            return prompt.text
        return f"{prompt.text}\n\n{options}"

    @classmethod
    def _with_prefix(cls, prefix: str, text: str) -> str:
        return f"{prefix}\n\n{text}"
