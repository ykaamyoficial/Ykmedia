// Sem isto o Windows anexa um console ao executavel e uma janela preta abre
// junto do app, mostrando o que o Rust escreve em stderr. Em debug o console
// continua util para acompanhar os logs.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    ykmedia_lib::run()
}
