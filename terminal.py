import json
import uuid
import time
import os
from communicator import handle_message, receive_from_ai
import config  # shared config with WORKING_DIR

class TerminalSession:
    def __init__(self, response_timeout=20):
        self.response_timeout = response_timeout
        self.conversation = {
            "message": "Hello! How can I assist you today?",
            "action": [],
            "data": "",
            "history": [],
            "folder": {},
            "error": "",
            "session_id": str(uuid.uuid4()),
            "target": ["ai"]
        }

        # Ensure input is always in sync with folder at start
        self.update_input_with_folder_tree()

    def set_working_directory(self, path):
        """Update global folder and rebuild input tree immediately."""
        if os.path.isdir(path):
            config.WORKING_DIR = path
            self.conversation["folder"] = path
            self.update_input_with_folder_tree()  # rebuild input for new folder
            print(f"Working directory set to: {config.WORKING_DIR}")
        else:
            print(f"Invalid directory: {path}")

    def build_folder_tree(self, path):
        """Return a clean tree view of folders and files without reading contents."""
        tree = {}
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    tree[entry.name] = self.build_folder_tree(os.path.join(path, entry.name))
                else:
                    tree[entry.name] = {}  # just placeholder for file
        except Exception as e:
            tree = {"error": str(e)}
        return tree

    def update_input_with_folder_tree(self):
        """Clear previous input and rebuild tree from current folder."""
        self.conversation["input"] = {}  # clear old input
        tree = self.build_folder_tree(config.WORKING_DIR)
        self.conversation["input"] = tree

    def get_response(self):
        """Wait for any response from communicator for terminal."""
        start_time = time.time()
        while time.time() - start_time < self.response_timeout:
            response_json = receive_from_ai()
            if response_json:
                try:
                    response = json.loads(response_json)
                    if "terminal" in response.get("target", []):
                        response["error"] = ""  # clear errors for display
                        return response
                except json.JSONDecodeError:
                    print("Received invalid JSON from communicator")
            time.sleep(0.10)
        return None

    def start(self):
        print(f"Session ID: {self.conversation['session_id']}")
        print("AI:", self.conversation["message"])

        while True:
            user_input = input("You: ").strip()

            # Change working directory
            if user_input.lower().startswith("cd "):
                new_dir = user_input[3:].strip()
                self.set_working_directory(new_dir)
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Ending session.")
                break

            # Preserve history & data
            preserved_history = self.conversation.get("history", [])
            preserved_data = self.conversation.get("data", "")

            # Update conversation
            self.conversation["message"] = user_input
            self.conversation["target"] = ["ai"]
            self.update_input_with_folder_tree()  # ensure input reflects current folder
            self.conversation["history"] = preserved_history
            self.conversation["data"] = preserved_data

            # Send to communicator
            handle_message(json.dumps(self.conversation))

            # Wait for response
            response = self.get_response()
            if not response:
                print("AI: [No response within timeout]")
                continue

            # Update conversation JSON but preserve history/data from response
            response_history = response.get("history", [])
            response_data = response.get("data", "")
            self.conversation.update(response)
            self.conversation["history"] = response_history
            self.conversation["data"] = response_data

            # Print entire JSON response
            print("AI JSON Response:", json.dumps(self.conversation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    TerminalSession().start()
