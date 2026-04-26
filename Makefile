create_venv:
	python -m venv venv
activate_venv:
	.\venv\Scripts\activate
install_requirements:
	pip install -r requirements.txt