from src.services.edutwin_service import EduTwinService


def main():
    service = EduTwinService()

    result = service.process_message(
        "recommend a cooking videos"
    )
    print("\n========== ANSWER ==========\n")
    print(result["answer"])

    print("\n========== MEMORY ==========\n")
    print(result["memory_created"])

    print("\n========== BRIEFING ==========\n")
    print(result["brief"])


if __name__ == "__main__":
    main()