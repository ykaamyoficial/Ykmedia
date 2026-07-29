use std::path::Path;
use std::process::Command;

#[tauri::command]
fn open_media_file(path: String) -> Result<(), String> {
    open_path(&path)
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
        Command::new("cmd")
            .args(["/C", "start", "", path])
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
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![open_media_file, reveal_media_file])
        .run(tauri::generate_context!())
        .expect("failed to run YkMedia Tauri application");
}
