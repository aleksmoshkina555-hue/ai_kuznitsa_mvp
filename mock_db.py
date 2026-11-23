CORP_SOURCES = [
    {
        "id": "DOC-2024-09",
        "source_type": "Регламент",
        "title": "Регламент согласования договоров (ред. 2024)",
        "date": "15.03.2024",
        "status": "Устарел",
        "owner": "Юридический отдел",
        "content": "Агентские договоры на любую сумму подписывает руководитель отдела закупок Петров А.В. Срок согласования — 5 рабочих дней."
    },
    {
        "id": "ORD-2026-118",
        "source_type": "Приказ",
        "title": "Приказ №118-П «О новом порядке подписания агентских договоров»",
        "date": "10.02.2026",
        "status": "Действует",
        "owner": "Департамент правового обеспечения (Кузнецова Е.С.)",
        "content": "С февраля 2026 года агентские договоры до 500 000 руб. подписывает коммерческий директор Смирнов И.О. Договоры свыше 500 000 руб. подписывает генеральный директор. Старый регламент 2024 года считать утратившим силу."
    },
    {
        "id": "MAIL-2026-402",
        "source_type": "Корпоративная почта",
        "title": "Письмо: Изменение ответственного за проверку контрагентов и ЭДО",
        "date": "12.10.2026",
        "status": "Действует",
        "owner": "Бухгалтерия (Волкова М.Н.)",
        "content": "Коллеги, напоминаю, что за этап проверки контрагента в ЭДО перед подписанием агентского договора теперь отвечает ведущий бухгалтер Волкова М.Н. (доб. 4412)."
    },
    {
        "id": "CHAT-2026-89",
        "source_type": "Рабочий чат",
        "title": "Закреп в канале #юристы-договоры",
        "date": "01.11.2026",
        "status": "Действует",
        "owner": "Юрист Соколов Д.А.",
        "content": "Актуальный шаблон агентского договора находится на сетевом диске S:\\Templates\\2026. Без листа согласования от бухгалтерии договоры на подпись не принимаются."
    }
]


def search_knowledge_base(query: str) -> tuple[list, list]:
    keywords = [word.lower().strip(".,!?()«»") for word in query.split() if len(word) > 3]
    active_matches = []
    outdated_matches = []

    for source in CORP_SOURCES:
        searchable_text = f"{source['title']} {source['content']} {source['owner']}".lower()
        relevance_score = sum(1 for keyword in keywords if keyword in searchable_text)
        if relevance_score > 0:
            if source["status"] == "Действует":
                active_matches.append((relevance_score, source))
            else:
                outdated_matches.append((relevance_score, source))

    active_matches.sort(key=lambda item: item[0], reverse=True)
    outdated_matches.sort(key=lambda item: item[0], reverse=True)

    return [item[1] for item in active_matches], [item[1] for item in outdated_matches]
