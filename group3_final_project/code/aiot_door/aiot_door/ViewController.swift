//
//  ViewController.swift
//  aiot_door
//
//  Created by 李焰堃 on 12/5/25.
//

import UIKit
import AVFoundation

class ViewController: UIViewController {
    
    // Server port
    let serverPort = "8080"
    
    // IP address text field
    var ipTextField: UITextField!
    
    // Button array
    var buttons: [UIButton] = []
    
    // UserDefaults key
    let savedIPKey = "SavedServerIP"
    let savedGeminiKey = "SavedGeminiKey"
    
    // Recording related
    var recordingButton: UIButton!
    var audioRecorder: AVAudioRecorder?
    var audioSession: AVAudioSession!
    var isRecording = false
    var recordingURL: URL?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupAudioSession()
        setupUI()
        loadSavedIP()
    }
    
    func setupAudioSession() {
        audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }
    
    func setupUI() {
        view.backgroundColor = UIColor.systemBackground
        
        // Create settings button in top right
        let settingsButton = UIBarButtonItem(image: UIImage(systemName: "gearshape"), style: .plain, target: self, action: #selector(showSettings))
        navigationItem.rightBarButtonItem = settingsButton
        
        // Create title
        let titleLabel = UILabel()
        titleLabel.text = "Smart Door Lock Control"
        titleLabel.font = UIFont.systemFont(ofSize: 24, weight: .bold)
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(titleLabel)
        
        // Create IP input area container
        let ipContainerView = UIView()
        ipContainerView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(ipContainerView)
        
        // IP address label
        let ipLabel = UILabel()
        ipLabel.text = "Server IP:"
        ipLabel.font = UIFont.systemFont(ofSize: 16, weight: .medium)
        ipLabel.translatesAutoresizingMaskIntoConstraints = false
        ipContainerView.addSubview(ipLabel)
        
        // IP address text field
        ipTextField = UITextField()
        ipTextField.placeholder = "e.g.: 10.206.168.73"
        ipTextField.borderStyle = .roundedRect
        ipTextField.keyboardType = .numbersAndPunctuation
        ipTextField.autocorrectionType = .no
        ipTextField.autocapitalizationType = .none
        ipTextField.font = UIFont.systemFont(ofSize: 16)
        ipTextField.clearButtonMode = .whileEditing
        ipTextField.translatesAutoresizingMaskIntoConstraints = false
        ipContainerView.addSubview(ipTextField)
        
        // Button configuration
        let buttonTitles = [
            ("Lock", "lock", UIColor.systemBlue),
            ("Unlock", "unlock", UIColor.systemGreen),
            ("Change Password", "change_password", UIColor.systemOrange),
            ("Take Photo", "take_photo", UIColor.systemPurple),
            ("Display Text", "display_text", UIColor.systemTeal),
        ]
        
        var previousButton: UIButton?
        
        // Create four buttons
        for (index, (title, command, color)) in buttonTitles.enumerated() {
            let button = createButton(title: title, command: command, color: color, index: index)
            buttons.append(button)
            view.addSubview(button)
            
            NSLayoutConstraint.activate([
                button.centerXAnchor.constraint(equalTo: view.centerXAnchor),
                button.widthAnchor.constraint(equalToConstant: 200),
                button.heightAnchor.constraint(equalToConstant: 60)
            ])
            
            if let previous = previousButton {
                button.topAnchor.constraint(equalTo: previous.bottomAnchor, constant: 20).isActive = true
            } else {
                button.topAnchor.constraint(equalTo: ipContainerView.bottomAnchor, constant: 40).isActive = true
            }
            
            previousButton = button
        }
        
        // Create recording button
        recordingButton = UIButton(type: .system)
        recordingButton.setTitle("Start Recording", for: .normal)
        recordingButton.titleLabel?.font = UIFont.systemFont(ofSize: 20, weight: .semibold)
        recordingButton.backgroundColor = UIColor.systemRed
        recordingButton.setTitleColor(.white, for: .normal)
        recordingButton.layer.cornerRadius = 12
        recordingButton.translatesAutoresizingMaskIntoConstraints = false
        recordingButton.addAction(UIAction { [weak self] _ in
            self?.toggleRecording()
        }, for: .touchUpInside)
        view.addSubview(recordingButton)
        
        // Setup constraints
        NSLayoutConstraint.activate([
            // Title
            titleLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            titleLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            titleLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            
            // IP container
            ipContainerView.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 30),
            ipContainerView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 40),
            ipContainerView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -40),
            ipContainerView.heightAnchor.constraint(equalToConstant: 80),
            
            // IP label
            ipLabel.topAnchor.constraint(equalTo: ipContainerView.topAnchor, constant: 10),
            ipLabel.leadingAnchor.constraint(equalTo: ipContainerView.leadingAnchor),
            ipLabel.trailingAnchor.constraint(equalTo: ipContainerView.trailingAnchor),
            
            // IP text field
            ipTextField.topAnchor.constraint(equalTo: ipLabel.bottomAnchor, constant: 8),
            ipTextField.leadingAnchor.constraint(equalTo: ipContainerView.leadingAnchor),
            ipTextField.trailingAnchor.constraint(equalTo: ipContainerView.trailingAnchor),
            ipTextField.heightAnchor.constraint(equalToConstant: 44),
            
            // Recording button
            recordingButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            recordingButton.widthAnchor.constraint(equalToConstant: 200),
            recordingButton.heightAnchor.constraint(equalToConstant: 60)
        ])
        
        // Set recording button top constraint based on last button
        if let lastButton = buttons.last {
            recordingButton.topAnchor.constraint(equalTo: lastButton.bottomAnchor, constant: 20).isActive = true
        } else {
            recordingButton.topAnchor.constraint(equalTo: ipContainerView.bottomAnchor, constant: 40).isActive = true
        }
        
        // Add tap gesture to dismiss keyboard
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(dismissKeyboard))
        tapGesture.cancelsTouchesInView = false
        view.addGestureRecognizer(tapGesture)
    }
    
    @objc func dismissKeyboard() {
        view.endEditing(true)
    }
    
    func createButton(title: String, command: String, color: UIColor, index: Int) -> UIButton {
        let button = UIButton(type: .system)
        button.setTitle(title, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 20, weight: .semibold)
        button.backgroundColor = color
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 12
        button.translatesAutoresizingMaskIntoConstraints = false
        
        // Add tap event
        button.addAction(UIAction { [weak self] _ in
            if command == "change_password" {
                // Change password button needs to show input dialog
                self?.showPasswordInputDialog()
            } else if command == "display_text" {
                // Display text button needs to show text input dialog
                self?.showTextInputDialog()
            } else if command == "take_photo" {
                // Take photo button needs to send POST request and display image
                self?.sendTakePhotoCommand()
            } else {
                self?.sendCommand(command: command)
            }
        }, for: .touchUpInside)
        
        return button
    }
    
    func sendCommand(command: String, parameter: String? = nil) {
        // Get the current IP address input
        guard let serverIP = ipTextField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
              !serverIP.isEmpty else {
            showAlert(message: "Please enter server IP address")
            return
        }
        
        // Save IP address
        saveIP(serverIP)
        
        // Build URL using URLComponents to ensure proper encoding
        var urlComponents = URLComponents()
        urlComponents.scheme = "http"
        urlComponents.host = serverIP
        urlComponents.port = Int(serverPort)
        urlComponents.path = "/\(command)"
        
        // If parameter exists, add as query parameter
        if let param = parameter {
            urlComponents.queryItems = [
                URLQueryItem(name: "password", value: param)
            ]
        }
        
        guard let url = urlComponents.url else {
            showAlert(message: "Invalid URL address")
            return
        }
        
        // Create URL request
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 10.0
        request.cachePolicy = .reloadIgnoringLocalCacheData
        
        // Create URLSession configuration that allows HTTP
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10.0
        config.timeoutIntervalForResource = 10.0
        let session = URLSession(configuration: config)
        
        // Send request
        let task = session.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    let errorMsg = error.localizedDescription
                    print("Network error: \(errorMsg)")
                    print("URL: \(url.absoluteString)")
                    self?.showAlert(message: "Request failed: \(errorMsg)\n\nMake sure:\n1. Phone and server are on same WiFi\n2. Server IP is correct\n3. Server is running on port 8080")
                    return
                }
                
                if let httpResponse = response as? HTTPURLResponse {
                    print("Response status: \(httpResponse.statusCode)")
                    if httpResponse.statusCode == 200 {
                        let message = parameter != nil ? "Command \(command) with parameter \(parameter!) sent successfully!" : "Command \(command) sent successfully!"
                        self?.showAlert(message: message)
                    } else {
                        self?.showAlert(message: "Server returned error: \(httpResponse.statusCode)")
                    }
                } else {
                    let message = parameter != nil ? "Command \(command) with parameter \(parameter!) sent" : "Command \(command) sent"
                    self?.showAlert(message: message)
                }
            }
        }
        
        task.resume()
    }
    
    func showPasswordInputDialog() {
        let alert = UIAlertController(title: "Change Password", message: "Please enter new password (numbers only)", preferredStyle: .alert)
        
        alert.addTextField { textField in
            textField.placeholder = "Enter numeric password"
            textField.keyboardType = .numberPad
        }
        
        let confirmAction = UIAlertAction(title: "OK", style: .default) { [weak self] _ in
            if let textField = alert.textFields?.first,
               let password = textField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
               !password.isEmpty {
                // Validate if it's numeric only
                if password.range(of: "^[0-9]+$", options: .regularExpression) != nil {
                    self?.sendCommand(command: "change_password", parameter: password)
                } else {
                    self?.showAlert(message: "Password must be numbers only")
                }
            } else {
                self?.showAlert(message: "Please enter password")
            }
        }
        
        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel)
        
        alert.addAction(confirmAction)
        alert.addAction(cancelAction)
        
        present(alert, animated: true)
    }
    
    func showTextInputDialog() {
        let alert = UIAlertController(title: "Display Text on OLED", message: "Enter text to display on ESP32 OLED screen", preferredStyle: .alert)
        
        alert.addTextField { textField in
            textField.placeholder = "Enter text (max 20 characters)"
            textField.autocapitalizationType = .sentences
        }
        
        let confirmAction = UIAlertAction(title: "Display", style: .default) { [weak self] _ in
            if let textField = alert.textFields?.first,
               let text = textField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
               !text.isEmpty {
                // Limit text length to 20 characters
                let displayText = String(text.prefix(20))
                self?.sendDisplayTextCommand(text: displayText)
            } else {
                self?.showAlert(message: "Please enter text")
            }
        }
        
        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel)
        
        alert.addAction(confirmAction)
        alert.addAction(cancelAction)
        
        present(alert, animated: true)
    }
    
    func sendDisplayTextCommand(text: String) {
        // Get the current IP address input
        guard let serverIP = ipTextField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
              !serverIP.isEmpty else {
            showAlert(message: "Please enter server IP address")
            return
        }
        
        // Save IP address
        saveIP(serverIP)
        
        // Build URL
        var urlComponents = URLComponents()
        urlComponents.scheme = "http"
        urlComponents.host = serverIP
        urlComponents.port = Int(serverPort)
        urlComponents.path = "/mobile_command"
        
        guard let url = urlComponents.url else {
            showAlert(message: "Invalid URL address")
            return
        }
        
        // Create POST request with JSON body
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10.0
        request.cachePolicy = .reloadIgnoringLocalCacheData
        
        // Create JSON body with display_text command and text
        let jsonBody: [String: String] = [
            "command": "display_text",
            "text": text
        ]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: jsonBody) else {
            showAlert(message: "Failed to create request body")
            return
        }
        request.httpBody = jsonData
        
        // Create URLSession configuration that allows HTTP
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10.0
        config.timeoutIntervalForResource = 10.0
        let session = URLSession(configuration: config)
        
        // Send request
        let task = session.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    let errorMsg = error.localizedDescription
                    print("Network error: \(errorMsg)")
                    print("URL: \(url.absoluteString)")
                    self?.showAlert(message: "Request failed: \(errorMsg)\n\nMake sure:\n1. Phone and server are on same WiFi\n2. Server IP is correct\n3. Server is running on port 8080")
                    return
                }
                
                guard let data = data else {
                    self?.showAlert(message: "No data received")
                    return
                }
                
                // Parse JSON response
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let status = json["status"] as? String {
                        if status == "success" {
                            self?.showAlert(message: "Text sent successfully!")
                        } else {
                            let message = json["message"] as? String ?? "Failed to send text"
                            self?.showAlert(message: message)
                        }
                    }
                } catch {
                    self?.showAlert(message: "Failed to parse server response: \(error.localizedDescription)")
                }
            }
        }
        
        task.resume()
    }
    
    func sendTakePhotoCommand() {
        // Get the current IP address input
        guard let serverIP = ipTextField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
              !serverIP.isEmpty else {
            showAlert(message: "Please enter server IP address")
            return
        }
        
        // Save IP address
        saveIP(serverIP)
        
        // Build URL
        var urlComponents = URLComponents()
        urlComponents.scheme = "http"
        urlComponents.host = serverIP
        urlComponents.port = Int(serverPort)
        urlComponents.path = "/mobile_command"
        
        guard let url = urlComponents.url else {
            showAlert(message: "Invalid URL address")
            return
        }
        
        // Create POST request with JSON body
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0
        request.cachePolicy = .reloadIgnoringLocalCacheData
        
        // Create JSON body
        let jsonBody: [String: String] = ["command": "take_photo"]
        guard let jsonData = try? JSONSerialization.data(withJSONObject: jsonBody) else {
            showAlert(message: "Failed to create request body")
            return
        }
        request.httpBody = jsonData
        
        // Create URLSession configuration that allows HTTP
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30.0
        config.timeoutIntervalForResource = 30.0
        let session = URLSession(configuration: config)
        
        // Send request
        let task = session.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    let errorMsg = error.localizedDescription
                    print("Network error: \(errorMsg)")
                    print("URL: \(url.absoluteString)")
                    self?.showAlert(message: "Request failed: \(errorMsg)\n\nMake sure:\n1. Phone and server are on same WiFi\n2. Server IP is correct\n3. Server is running on port 8080")
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    self?.showAlert(message: "No data received")
                }
                return
            }
            
            // Parse JSON response
            do {
                guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let status = json["status"] as? String else {
                    DispatchQueue.main.async {
                        self?.showAlert(message: "Invalid response format")
                    }
                    return
                }
                
                if status == "success",
                   let imageBase64 = json["image_base64"] as? String {
                    // Decode base64 image
                    if let imageData = Data(base64Encoded: imageBase64),
                       let image = UIImage(data: imageData) {
                        DispatchQueue.main.async {
                            self?.showPhoto(image: image)
                        }
                    } else {
                        DispatchQueue.main.async {
                            self?.showAlert(message: "Failed to decode image")
                        }
                    }
                } else {
                    let message = json["message"] as? String ?? "Failed to take photo"
                    DispatchQueue.main.async {
                        self?.showAlert(message: message)
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    self?.showAlert(message: "Failed to parse response: \(error.localizedDescription)")
                }
            }
        }
        
        task.resume()
    }
    
    func showPhoto(image: UIImage) {
        // Make sure to close any existing Alert first
        if let presented = presentedViewController {
            presented.dismiss(animated: false) { [weak self] in
                self?.presentPhotoAlert(image: image)
            }
        } else {
            presentPhotoAlert(image: image)
        }
    }
    
    func presentPhotoAlert(image: UIImage) {
        let alert = UIAlertController(title: "Photo", message: nil, preferredStyle: .alert)
        
        // Create image view
        let imageView = UIImageView(frame: CGRect(x: 0, y: 0, width: 270, height: 270))
        imageView.image = image
        imageView.contentMode = .scaleAspectFit
        imageView.backgroundColor = .black
        
        // Set alert view to fit image
        alert.view.addSubview(imageView)
        alert.view.heightAnchor.constraint(equalToConstant: 320).isActive = true
        
        // Add constraints
        imageView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            imageView.centerXAnchor.constraint(equalTo: alert.view.centerXAnchor),
            imageView.topAnchor.constraint(equalTo: alert.view.topAnchor, constant: 50),
            imageView.widthAnchor.constraint(equalToConstant: 270),
            imageView.heightAnchor.constraint(equalToConstant: 270)
        ])
        
        let okAction = UIAlertAction(title: "OK", style: .default)
        alert.addAction(okAction)
        
        present(alert, animated: true)
    }
    
    func saveIP(_ ip: String) {
        UserDefaults.standard.set(ip, forKey: savedIPKey)
    }
    
    func loadSavedIP() {
        if let savedIP = UserDefaults.standard.string(forKey: savedIPKey) {
            ipTextField.text = savedIP
        } else {
            // If no saved IP, set default value
            ipTextField.text = "10.206.168.73"
        }
    }
    
    func showAlert(message: String) {
        // Make sure to close any existing Alert first
        if let presented = presentedViewController {
            presented.dismiss(animated: false) { [weak self] in
                self?.presentAlert(message: message)
            }
        } else {
            presentAlert(message: message)
        }
    }
    
    func presentAlert(message: String) {
        let alert = UIAlertController(title: "Alert", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
    
    // MARK: - Recording Functions
    
    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }
    
    func startRecording() {
        // Request microphone permission
        audioSession.requestRecordPermission { [weak self] granted in
            guard let self = self else { return }
            if granted {
                DispatchQueue.main.async {
                    self.doStartRecording()
                }
            } else {
                DispatchQueue.main.async {
                    self.showAlert(message: "Microphone permission is required for recording")
                }
            }
        }
    }
    
    func doStartRecording() {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioFilename = documentsPath.appendingPathComponent("recording.m4a")
        recordingURL = audioFilename
        
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
            audioRecorder?.record()
            isRecording = true
            recordingButton.setTitle("Stop Recording", for: .normal)
            recordingButton.backgroundColor = UIColor.systemGray
        } catch {
            showAlert(message: "Recording failed: \(error.localizedDescription)")
        }
    }
    
    func stopRecording() {
        audioRecorder?.stop()
        isRecording = false
        recordingButton.setTitle("Start Recording", for: .normal)
        recordingButton.backgroundColor = UIColor.systemRed
        
        guard let recordingURL = recordingURL else { return }
        
        // Process recording with OpenAI
        processRecording(url: recordingURL)
    }
    
    // MARK: - OpenAI Functions
    
    func processRecording(url: URL) {
        showAlert(message: "Processing recording...")
        
        // First, transcribe audio to text using Whisper API
        transcribeAudio(url: url) { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .success(let transcript):
                // Then, use GPT to parse the command
                self.parseCommandWithGPT(transcript: transcript) { [weak self] command, password, error in
                    DispatchQueue.main.async {
                        guard let self = self else { return }
                        
                        if let error = error {
                            self.showAlert(message: error)
                            return
                        }
                        
                        if let command = command {
                            // Execute the command
                            if command == "change_password", let password = password {
                                self.sendCommand(command: "change_password", parameter: password)
                            } else if command == "take_photo" {
                                self.sendTakePhotoCommand()
                            } else {
                                self.sendCommand(command: command)
                            }
                        } else {
                            self.showAlert(message: "Unable to recognize command. Please say: lock, unlock, change password, or take photo")
                        }
                    }
                }
            case .failure(let error):
                DispatchQueue.main.async {
                    self.showAlert(message: error)
                }
            }
        }
    }
    
    enum TranscriptionResult {
        case success(String)
        case failure(String)
    }
    
    func transcribeAudio(url: URL, completion: @escaping (TranscriptionResult) -> Void) {
        guard let apiKey = UserDefaults.standard.string(forKey: savedGeminiKey), !apiKey.isEmpty else {
            completion(.failure("Gemini API key not configured. Please set your API key in Settings.\n\nGet your API key from: https://makersuite.google.com/app/apikey"))
            return
        }
        
        // Read audio file
        guard let audioData = try? Data(contentsOf: url) else {
            completion(.failure("Recognition fail: Unable to read audio file"))
            return
        }
        
        // Use Gemini for audio transcription (Gemini 1.5 Pro supports audio)
        // Convert audio to base64
        let audioBase64 = audioData.base64EncodedString()
        
        // Create request to Gemini API
        // Use v1 API with gemini-2.5-flash model
        let apiURL = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=\(apiKey)")!
        var request = URLRequest(url: apiURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 60.0
        
        // Gemini API request body for audio transcription
        let requestBody: [String: Any] = [
            "contents": [
                [
                    "parts": [
                        [
                            "text": "Transcribe this audio to text. Return only the transcribed text, nothing else."
                        ],
                        [
                            "inline_data": [
                                "mime_type": "audio/m4a",
                                "data": audioBase64
                            ]
                        ]
                    ]
                ]
            ]
        ]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: requestBody) else {
            completion(.failure("Recognition fail: Failed to create request body"))
            return
        }
        
        request.httpBody = jsonData
        
        // Send request
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Transcription error: \(error)")
                completion(.failure("Recognition fail: Network error - \(error.localizedDescription)"))
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure("Recognition fail: Invalid HTTP response"))
                return
            }
            
            let responseString = String(data: data ?? Data(), encoding: .utf8) ?? ""
            
            // Log response for debugging
            print("Gemini API Response Status: \(httpResponse.statusCode)")
            if httpResponse.statusCode != 200 {
                print("Gemini API Error Response: \(responseString)")
            }
            
            guard httpResponse.statusCode == 200 else {
                // Parse error response
                if let data = data,
                   let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let error = errorJson["error"] as? [String: Any],
                   let errorMessage = error["message"] as? String {
                    completion(.failure("Recognition fail: Gemini API Error - \(errorMessage)"))
                } else {
                    completion(.failure("Recognition fail: Gemini API returned error: HTTP \(httpResponse.statusCode)\n\(responseString.prefix(300))"))
                }
                return
            }
            
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let candidates = json["candidates"] as? [[String: Any]],
                  let firstCandidate = candidates.first,
                  let content = firstCandidate["content"] as? [String: Any],
                  let parts = content["parts"] as? [[String: Any]],
                  let firstPart = parts.first,
                  let text = firstPart["text"] as? String else {
                completion(.failure("Recognition fail: Unable to parse transcription response"))
                return
            }
            
            let transcribedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if transcribedText.isEmpty {
                completion(.failure("Recognition fail: Empty transcription result"))
                return
            }
            
            completion(.success(transcribedText))
        }
        
        task.resume()
    }
    
    func parseCommandWithGPT(transcript: String, completion: @escaping (String?, String?, String?) -> Void) {
        guard let apiKey = UserDefaults.standard.string(forKey: savedGeminiKey), !apiKey.isEmpty else {
            completion(nil, nil, "Gemini API key not configured. Please set your API key in Settings.")
            return
        }
        
        // Create request to Gemini API
        // Use v1 API with gemini-2.5-flash model (fast, cheap, perfect for command parsing)
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=\(apiKey)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 60.0
        
        let prompt = """
        Analyze the following speech-to-text content and determine the user's intent. Return only one of the following four commands:
        - lock: if the user wants to lock
        - unlock: if the user wants to unlock
        - change_password: if the user wants to change password (must also extract the new password, format: change_password|new_password, e.g., change_password|1234)
        - take_photo: if the user wants to take a photo
        
        If unable to recognize as one of the above four commands, return "unknown".
        
        Speech content: \(transcript)
        
        Return only the command, no other text. If it's change_password, the format must be: change_password|password_numbers
        """
        
        let requestBody: [String: Any] = [
            "contents": [
                [
                    "parts": [
                        [
                            "text": prompt
                        ]
                    ]
                ]
            ],
            "generationConfig": [
                "temperature": 0.3,
                "maxOutputTokens": 50
            ]
        ]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: requestBody) else {
            completion(nil, nil, "Recognition fail: Failed to create request body")
            return
        }
        
        request.httpBody = jsonData
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Gemini parsing error: \(error)")
                completion(nil, nil, "Recognition fail: Network error - \(error.localizedDescription)")
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                completion(nil, nil, "Recognition fail: Invalid HTTP response")
                return
            }
            
            let responseString = String(data: data ?? Data(), encoding: .utf8) ?? ""
            
            // Log response for debugging
            print("Gemini API Response Status: \(httpResponse.statusCode)")
            if httpResponse.statusCode != 200 {
                print("Gemini API Error Response: \(responseString)")
            }
            
            guard httpResponse.statusCode == 200 else {
                // Parse error response
                if let data = data,
                   let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let error = errorJson["error"] as? [String: Any],
                   let errorMessage = error["message"] as? String {
                    completion(nil, nil, "Recognition fail: Gemini API Error - \(errorMessage)")
                } else {
                    completion(nil, nil, "Recognition fail: Gemini API returned error: HTTP \(httpResponse.statusCode)\n\(responseString.prefix(300))")
                }
                return
            }
            
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let candidates = json["candidates"] as? [[String: Any]],
                  let firstCandidate = candidates.first,
                  let content = firstCandidate["content"] as? [String: Any],
                  let parts = content["parts"] as? [[String: Any]],
                  let firstPart = parts.first,
                  let text = firstPart["text"] as? String else {
                completion(nil, nil, "Recognition fail: Unable to parse command response")
                return
            }
            
            let trimmedContent = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            
            // Parse the response
            if trimmedContent.contains("change_password") {
                let parts = trimmedContent.split(separator: "|")
                if parts.count == 2 {
                    let password = String(parts[1]).trimmingCharacters(in: .whitespacesAndNewlines)
                    // Validate password is numeric
                    if password.range(of: "^[0-9]+$", options: .regularExpression) != nil {
                        completion("change_password", password, nil)
                    } else {
                        completion(nil, nil, "Recognition fail: Invalid password format")
                    }
                } else {
                    completion(nil, nil, "Recognition fail: Unable to extract password from change_password command")
                }
            } else if trimmedContent == "lock" || trimmedContent.contains("lock") {
                completion("lock", nil, nil)
            } else if trimmedContent == "unlock" || trimmedContent.contains("unlock") {
                completion("unlock", nil, nil)
            } else if trimmedContent == "take_photo" || trimmedContent.contains("photo") {
                completion("take_photo", nil, nil)
            } else {
                completion(nil, nil, nil) // No error, just unrecognized command
            }
        }
        
        task.resume()
    }
    
    // MARK: - Settings
    
    @objc func showSettings() {
        let alert = UIAlertController(title: "Settings", message: "Enter Gemini API Key", preferredStyle: .alert)
        
        alert.addTextField { textField in
            textField.placeholder = "AIza..."
            textField.text = UserDefaults.standard.string(forKey: self.savedGeminiKey) ?? ""
            textField.autocapitalizationType = .none
            textField.autocorrectionType = .no
        }
        
        let saveAction = UIAlertAction(title: "Save", style: .default) { [weak self] _ in
            if let textField = alert.textFields?.first,
               let apiKey = textField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
               !apiKey.isEmpty {
                UserDefaults.standard.set(apiKey, forKey: self?.savedGeminiKey ?? "")
                self?.showAlert(message: "API Key saved")
            }
        }
        
        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel)
        
        alert.addAction(saveAction)
        alert.addAction(cancelAction)
        
        present(alert, animated: true)
    }
}

