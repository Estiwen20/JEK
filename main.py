import sys
from PyQt6.QtWidgets import QApplication
from database.connection import init_db
from repositories.usuario_repo import obtener_usuarios
from views.login_view import LoginView
from views.main_window import MainWindow
from views.primer_usuario_view import PrimerUsuarioView


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Restaurante")

    login = LoginView()
    main_window = None

    def abrir_app(usuario):
        nonlocal main_window
        login.hide()
        main_window = MainWindow(usuario)
        main_window.cerrar_sesion.connect(mostrar_login)
        main_window.show()

    def mostrar_login():
        login.input_usuario.clear()
        login.input_contrasena.clear()
        login.lbl_error.hide()
        login.show()

    login.login_exitoso.connect(abrir_app)

    # Si no hay usuarios, mostrar pantalla de configuración inicial
    if not obtener_usuarios():
        setup = PrimerUsuarioView()
        setup.usuario_creado.connect(mostrar_login)
        setup.show()
    else:
        login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()