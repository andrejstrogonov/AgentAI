from ResultFormatter import ResultFormatter


class UIInput:
    def prompts(self,system_prompt,user_prompt):
        system_prompt = (
            "Ты — эксперт в области разработки на Scala, Chisel, FIRRTL, Python, Tcl и проектирования цифровой аппаратуры "
            "на Verilog/VHDL для Intel Quartus Prime. Твоя задача — проанализировать предоставленный "
            "проект генератора, найти ошибки и сделать его полностью запускаемым."
        )

        user_query = (
            "Все уже сделано так, как ты говоришь, продолжи генерировать до успешного исполнения проекта.\n\n"
            f"Проект: {project_data}"
        )
        return ResultFormatter.display_results()