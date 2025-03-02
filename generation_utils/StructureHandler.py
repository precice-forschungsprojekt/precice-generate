from pathlib import Path
from .Logger import Logger
import shutil

class StructureHandler:
    def __init__(self, output_path: Path, clean_generated: bool = True) -> None:
        """ Creates the files and folders in a structure.
            :param clean_generated: If set to True, clean the _generated dir before the files are created.
            Can be useful if you added or adjusted files yourself and you are not sure what you changed."""
        # Objects
        self.root = output_path
        self.generated_root = self.root / "_generated"
        self.logger = Logger()

        # Create level 0 structure (everything in the root folder)
        if clean_generated:
            self._cleaner()
        self._create_folder_sturcture()
        self._create_level_0_structure()

    def _create_folder_sturcture(self) -> None:
        """Creates the structure needed for generated files"""
        try: 
            self.generated_root.mkdir(parents=True, exist_ok=True)
            self.logger.success(f"Created folder: {self.generated_root}")
        except Exception as create_folder_structure_excpetion:
            self.logger.error(f"Failed to create folder structure. Error: {create_folder_structure_excpetion}")

    def _create_level_0_structure(self) -> None:
        """Creates the necessary files of level 0 (everything in the root folder)."""

        # Files that need to be created
        files = [
            self.generated_root / "clean.sh",
            self.generated_root / "README.md",
            self.generated_root / "precice-config.xml",
        ]

        self.clean, self.README, self.precice_config = files

        for file in files:
            try:
                file.touch(exist_ok=True)
                self.logger.success(f"Created file: {file}")
            except Exception as create_files_exception:
                self.logger.error(f"Failed to create file {file}. Error: {create_files_exception}")

    def create_level_1_structure(self, participant: str, user_ui=None) -> list[Path]:
        """ Creates the necessary files of level 1 (everything in the generated sub-folders).
            :param participant: The participant for which the files should be created.
            :param user_ui: Optional UI_UserInput instance to retrieve participant information
            :return: participant_folder, adapter_config, run"""
        try:
            # Validate that user_ui is provided
            if user_ui is None:
                raise ValueError("user_ui must be provided to create level 1 structure")

            # Get the solver name from the participants
            solver_name = user_ui.participants[participant].solverName.lower()
            #folder name starts with lowercase
            participant = participant.lower()
            

            # Create the participant folder with name-solver format
            participant_folder = self.generated_root / f"{participant}-{solver_name}"
            participant_folder.mkdir(parents=True, exist_ok=True)
            self.logger.success(f"Created folder: {participant_folder}")

            # Create the adapter-config.json file
            adapter_config = participant_folder / "adapter-config.json"
            adapter_config.touch(exist_ok=True)
            self.logger.success(f"Created file: {adapter_config}")

            # Create the run.sh file
            self.run = participant_folder / "run.sh"
            self.run.touch(exist_ok=True)
            self.logger.success(f"Created file: {self.run}")

            return [participant_folder, adapter_config, self.run]
        except Exception as create_participant_folder_exception:
            # Define participant_folder before logging error
            participant_folder = self.generated_root / participant
            self.logger.error(f"Failed to create folder/file for participant: {participant_folder}. Error: {create_participant_folder_exception}")

    def _cleaner(self) -> None:
        """
        Removes the entire `self.generated_root` directory and its contents.
        If `self.generated_root` exists, it deletes everything inside it.
        """
        if self.generated_root.exists():
            try:
                # Remove the directory and all its contents
                shutil.rmtree(self.generated_root)
                self.logger.success(f"Successfully removed directory and all contents: {self.generated_root}")
            except Exception as cleaner_exception:
                self.logger.error(f"Failed to remove directory: {self.generated_root}. Error: {cleaner_exception}")
        else:
            self.logger.info(f"Directory {self.generated_root} does not exist. Nothing to clean.")