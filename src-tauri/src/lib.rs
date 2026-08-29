use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use tauri::{Manager, RunEvent, State};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

const BACKEND_PORT: u16 = 8010;
const BACKEND_SIDECAR_NAME: &str = "ykmedia-backend.exe";
const BACKEND_STARTUP_ATTEMPTS: u8 = 100;
const BACKEND_STARTUP_INTERVAL: Duration = Duration::from_millis(300);

#[derive(Clone, Default)]
struct BackendSidecarState {
    process: Arc<Mutex<Option<Child>>>,
}

#[tauri::command]
fn open_media_file(path: String) -> Result<(), String> {
    open_path(&path)
}

#[tauri::command]
fn api_token() -> Result<String, String> {
    let token_file = runtime_root()
        .map_err(|error| error.to_string())?
        .join("data")
        .join("api_token");

    for _ in 0..BACKEND_STARTUP_ATTEMPTS {
        if let Ok(content) = fs::read_to_string(&token_file) {
            let trimmed = content.trim();
            if !trimmed.is_empty() {
                return Ok(trimmed.to_string());
            }
        }
        std::thread::sleep(BACKEND_STARTUP_INTERVAL);
    }

    Err("O token da API do YkMedia nao ficou disponivel.".to_string())
}

#[tauri::command]
fn reveal_media_file(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        let target = Path::new(&path);
        let argument = if target.exists() {
            format!("/select,{}", target.display())
        } else {
            target
                .parent()
                .map(|parent| parent.display().to_string())
                .unwrap_or(path)
        };

        Command::new("explorer")
            .arg(argument)
            .spawn()
            .map_err(|error| error.to_string())?;
        return Ok(());
    }

    #[cfg(not(target_os = "windows"))]
    {
        open_path(&path)
    }
}

fn open_path(path: &str) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(path)
            .spawn()
            .map_err(|error| error.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(path)
            .spawn()
            .map_err(|error| error.to_string())?;
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        Command::new("xdg-open")
            .arg(path)
            .spawn()
            .map_err(|error| error.to_string())?;
    }

    Ok(())
}

pub fn run() {
    let backend_state = BackendSidecarState::default();
    let managed_state = backend_state.clone();

    tauri::Builder::default()
        .manage(backend_state)
        .setup(|app| {
            start_backend_sidecar(app.state::<BackendSidecarState>())?;
            schedule_system_preparation();
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            open_media_file,
            reveal_media_file,
            api_token
        ])
        .build(tauri::generate_context!())
        .expect("failed to initialize YkMedia Tauri application")
        .run(move |_, event| {
            if matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. }) {
                stop_backend_sidecar(&managed_state);
            }
        });
}

fn start_backend_sidecar(
    state: State<'_, BackendSidecarState>,
) -> Result<(), Box<dyn std::error::Error>> {
    if backend_is_healthy() {
        return Ok(());
    }

    let sidecar = backend_sidecar_path()?;
    if !sidecar.is_file() {
        #[cfg(debug_assertions)]
        return Ok(());

        #[cfg(not(debug_assertions))]
        return Err(format!("YkMedia backend sidecar was not found: {}", sidecar.display()).into());
    }

    let runtime_root = runtime_root()?;
    let stdout = backend_log_stream(&runtime_root);
    let stderr = backend_log_stream(&runtime_root);
    let mut command = Command::new(sidecar);
    command
        .env("YKMEDIA_RUNTIME_ROOT", runtime_root)
        .stdout(stdout)
        .stderr(stderr);
    #[cfg(target_os = "windows")]
    command.creation_flags(0x08000000);
    let child = command.spawn()?;

    let mut process = state
        .process
        .lock()
        .map_err(|_| "Could not acquire backend process lock")?;
    *process = Some(child);
    Ok(())
}

fn backend_log_stream(runtime_root: &Path) -> Stdio {
    let log_directory = runtime_root.join("logs");
    let log_file = log_directory.join("backend.log");
    fs::create_dir_all(log_directory)
        .and_then(|_| OpenOptions::new().create(true).append(true).open(log_file))
        .map(Stdio::from)
        .unwrap_or_else(|_| Stdio::null())
}

fn stop_backend_sidecar(state: &BackendSidecarState) {
    let Ok(mut process) = state.process.lock() else {
        return;
    };
    if let Some(mut child) = process.take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

fn backend_sidecar_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let executable = std::env::current_exe()?;
    let directory = executable
        .parent()
        .ok_or("Could not resolve YkMedia installation directory")?;
    Ok(directory.join(BACKEND_SIDECAR_NAME))
}

fn runtime_root() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let local_app_data = std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .ok_or("LOCALAPPDATA is not available")?;
    let root = local_app_data.join("YkMedia");
    std::fs::create_dir_all(&root)?;
    Ok(root)
}

fn backend_is_healthy() -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], BACKEND_PORT));
    let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(500)) else {
        return false;
    };
    if stream
        .set_read_timeout(Some(Duration::from_secs(2)))
        .and_then(|_| stream.set_write_timeout(Some(Duration::from_secs(2))))
        .is_err()
    {
        return false;
    }
    if stream
        .write_all(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
        .is_err()
    {
        return false;
    }

    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .is_ok_and(|_| response.starts_with("HTTP/1.1 200"))
}

fn schedule_system_preparation() {
    std::thread::spawn(|| {
        if !wait_for_backend_health() {
            eprintln!("YkMedia backend did not become available for automatic preparation.");
            return;
        }

        if let Err(error) = request_system_preparation() {
            eprintln!("YkMedia automatic system preparation failed: {error}");
        }
    });
}

fn wait_for_backend_health() -> bool {
    for _ in 0..BACKEND_STARTUP_ATTEMPTS {
        if backend_is_healthy() {
            return true;
        }
        std::thread::sleep(BACKEND_STARTUP_INTERVAL);
    }
    false
}

fn request_system_preparation() -> std::io::Result<()> {
    let address = SocketAddr::from(([127, 0, 0, 1], BACKEND_PORT));
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_secs(3))?;
    stream.set_write_timeout(Some(Duration::from_secs(10)))?;
    stream.set_read_timeout(Some(Duration::from_secs(1_200)))?;
    stream.write_all(
        b"POST /settings/prepare HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
    )?;

    let mut response = String::new();
    stream.read_to_string(&mut response)?;
    if response.starts_with("HTTP/1.1 2") {
        return Ok(());
    }

    Err(std::io::Error::other(
        "backend rejected the automatic preparation request",
    ))
}
