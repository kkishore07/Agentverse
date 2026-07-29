import asyncio
from devpilot.tui.app import DevPilotApp
from devpilot.tui.screens.models_screen import ModelsScreen

app = DevPilotApp()

async def run():
    async with app.run_test() as pilot:
        app.action_show_models()
        await pilot.pause(1)
        screen = app.screen
        if isinstance(screen, ModelsScreen):
            print(screen.tree)
            cards = screen.query("ModelCard")
            for card in cards:
                print(card, card.children)
                for child in card.children:
                    print("  ", child, child.styles.height, child.styles.width, getattr(child, "renderable", None))
        else:
            print("Not ModelsScreen:", screen)

asyncio.run(run())
