from app.models.interactive import InteractiveOption, InteractivePrompt
from app.services.category_service import CategoryService
from app.services.message_catalog import WhatsAppMessageCatalog


class InteractiveMenuBuilder:
    MAX_BUTTON_OPTIONS = 3
    MAX_LIST_OPTIONS = 10

    def build_category_menu(
        self,
        category_service: CategoryService,
        page: int = 1,
    ) -> InteractivePrompt:
        categories = category_service.list_categories()
        page = max(page, 1)
        start = (page - 1) * self.MAX_LIST_OPTIONS
        end = start + self.MAX_LIST_OPTIONS
        page_categories = categories[start:end]

        options = [
            InteractiveOption(
                id=f"category:{start + index}",
                title=self._short_title(category),
                description=category if len(category) > 20 else None,
            )
            for index, category in enumerate(page_categories, start=1)
        ]

        if end < len(categories):
            options.append(
                InteractiveOption(
                    id=f"action:next_page:{page + 1}",
                    title=WhatsAppMessageCatalog.next_page_title(),
                )
            )
        if page > 1:
            options.append(
                InteractiveOption(
                    id=f"action:previous_page:{page - 1}",
                    title=WhatsAppMessageCatalog.previous_page_title(),
                )
            )

        return InteractivePrompt(
            text=WhatsAppMessageCatalog.category_prompt(),
            options=options,
            footer=WhatsAppMessageCatalog.FOOTER,
            button_text=WhatsAppMessageCatalog.category_button_text(),
        )

    def build_filename_menu(self) -> InteractivePrompt:
        return InteractivePrompt(
            text=WhatsAppMessageCatalog.filename_prompt(),
            options=[
                InteractiveOption(
                    id="filename:keep_original",
                    title=WhatsAppMessageCatalog.keep_original_title(),
                ),
                InteractiveOption(
                    id="filename:custom",
                    title=WhatsAppMessageCatalog.custom_filename_title(),
                ),
            ],
            footer=WhatsAppMessageCatalog.FOOTER,
        )

    def build_collecting_menu(self) -> InteractivePrompt:
        return InteractivePrompt(
            text=WhatsAppMessageCatalog.collect_done_title(),
            options=[
                InteractiveOption(
                    id="collect:done",
                    title=WhatsAppMessageCatalog.collect_done_title(),
                ),
            ],
            footer=WhatsAppMessageCatalog.FOOTER,
        )

    def build_confirmation_menu(self) -> InteractivePrompt:
        return InteractivePrompt(
            text=WhatsAppMessageCatalog.invalid_confirmation(),
            options=[
                InteractiveOption(id="confirm:yes", title=WhatsAppMessageCatalog.confirm_title()),
                InteractiveOption(id="confirm:edit", title=WhatsAppMessageCatalog.correct_title()),
                InteractiveOption(id="confirm:cancel", title=WhatsAppMessageCatalog.cancel_title()),
            ],
            footer=WhatsAppMessageCatalog.FOOTER,
        )

    def build_help_menu(self) -> InteractivePrompt:
        return InteractivePrompt(
            text=WhatsAppMessageCatalog.help_prompt(),
            options=[
                InteractiveOption(id="command:status", title=WhatsAppMessageCatalog.status_title()),
                InteractiveOption(id="command:restart", title=WhatsAppMessageCatalog.restart_title()),
                InteractiveOption(id="command:cancel", title=WhatsAppMessageCatalog.cancel_title()),
            ],
            footer=WhatsAppMessageCatalog.FOOTER,
        )

    def _short_title(self, title: str) -> str:
        normalized = title.strip()
        if len(normalized) <= 20:
            return normalized
        return f"{normalized[:17].rstrip()}..."
