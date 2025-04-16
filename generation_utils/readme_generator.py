from pathlib import Path

class ReadmeGenerator:
        SOLVER_DOCS = {
            # CFD Solvers
            'openfoam': 'https://www.openfoam.com/documentation',
            'su2': 'https://su2code.github.io/docs/home/',
            'foam-extend': 'https://sourceforge.net/p/foam-extend/',
            
            # Structural Solvers
            'calculix': 'https://www.calculix.de/',
            'elmer': 'https://www.elmersolver.com/documentation/',
            'code_aster': 'https://www.code-aster.org/V2/doc/default/en/index.php',
            
            # Other Solvers
            'fenics': 'https://fenicsproject.org/docs/',
            'dealii': 'https://dealii.org/current/doxygen/deal.II/index.html',
            
            # Fallback
            'default': 'https://precice.org/adapter-list.html'
        }

    def generate_readme(self, file_generator):
        """Generates the README.md file with dynamic content based on simulation configuration"""
        logger = file_generator.logger
        user_ui = file_generator.user_ui
        
        # Read the template README with explicit UTF-8 encoding
        readme_template_path = Path(__file__).parent.parent / "templates" / "template_README.md"
        
        with open(readme_template_path, 'r', encoding='utf-8') as template_file:
            readme_content = template_file.read()

        # Extract participants and their solvers
        participants_list = []
        solvers_list = []
        solver_links = {}
        original_solver_names = {}

        # Ensure participants exist before processing
        if not hasattr(user_ui, 'participants') or not user_ui.participants:
            logger.warning("No participants found. Using default placeholders.")
            participants_list = ["DefaultParticipant"]
            solvers_list = ["DefaultSolver"]
            original_solver_names = {"defaultparticipant": "DefaultSolver"}
        else:
            for participant_name, participant_info in user_ui.participants.items():
                # Preserve original solver name
                original_solver_name = getattr(participant_info, 'solverName', 'UnknownSolver')
                solver_name = original_solver_name.lower()
                
                participants_list.append(participant_name)
                solvers_list.append(original_solver_name)
                original_solver_names[participant_name.lower()] = original_solver_name
                
                # Get solver documentation link, use default if not found
                solver_links[solver_name] = self.SOLVER_DOCS.get(solver_name, self.SOLVER_DOCS['default'])

        # Determine coupling strategy
        coupling_strategy = "Partitioned" if len(participants_list) > 1 else "Single Solver"

        # Replace placeholders
        readme_content = readme_content.replace("{PARTICIPANTS_LIST}", "\n  ".join(f"- {p}" for p in participants_list))
        readme_content = readme_content.replace("{SOLVERS_LIST}", "\n  ".join(f"- {s}" for s in solvers_list))
        readme_content = readme_content.replace("{COUPLING_STRATEGY}", coupling_strategy)
        
        # Explicitly replace solver-specific placeholders
        readme_content = readme_content.replace("{SOLVER1_NAME}", solvers_list[0] if solvers_list else "Solver1")
        readme_content = readme_content.replace("{SOLVER2_NAME}", solvers_list[1] if len(solvers_list) > 1 else "Solver2")
        
        # Generate adapter configuration paths for all participants
        adapter_config_paths = []
        
        for participant in participants_list:
            # Find the corresponding solver name for this participant
            solver_name = original_solver_names.get(participant.lower(), 'solver')
            adapter_config_paths.append(f"- **{participant}**: `{participant}-{solver_name}/adapter-config.json`")
        
        # Replace adapter configuration section
        readme_content = readme_content.replace(
            "- **Adapter Configuration**: `{PARTICIPANT_NAME}/adapter-config.json`", 
            "**Adapter Configurations**:\n" + "\n".join(adapter_config_paths)
        )
        
        # Explicitly replace solver links
        readme_content = readme_content.replace(
            "[Link1]", 
            f"[{solvers_list[0] if solvers_list else 'Solver1'}]({solver_links.get(solvers_list[0].lower(), '#') if solvers_list else '#'})"
        )
        readme_content = readme_content.replace(
            "[Link2]", 
            f"[{solvers_list[1] if len(solvers_list) > 1 else 'Solver2'}]({solver_links.get(solvers_list[1].lower(), '#') if len(solvers_list) > 1 else '#'})"
        )

        # Write the README
        structure = file_generator.get_structure()
        readme_path = structure.output_path / "README.md"
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as readme_file:
                readme_file.write(readme_content)
            logger.success(f"README.md generated successfully at {readme_path}")
            return readme_path
        except Exception as e:
            logger.error(f"Failed to write README.md: {str(e)}")
            return None