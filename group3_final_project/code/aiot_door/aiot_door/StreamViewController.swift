//
//  StreamViewController.swift
//  aiot_door
//
//  Created by 李焰堃 on 12/5/25.
//

import UIKit
import AVKit
import AVFoundation

class StreamViewController: UIViewController {
    
    var videoURL: String!
    var serverIP: String!
    var serverPort: String!
    var player: AVPlayer?
    var playerViewController: AVPlayerViewController!
    var closeButton: UIButton!
    var statusLabel: UILabel!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        requestVideo()
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        player?.pause()
        player = nil
    }
    
    func setupUI() {
        view.backgroundColor = .black
        
        // Player view controller for video playback
        playerViewController = AVPlayerViewController()
        playerViewController.view.backgroundColor = .black
        playerViewController.view.translatesAutoresizingMaskIntoConstraints = false
        addChild(playerViewController)
        view.addSubview(playerViewController.view)
        playerViewController.didMove(toParent: self)
        
        // Status label
        statusLabel = UILabel()
        statusLabel.text = "Requesting video..."
        statusLabel.textColor = .white
        statusLabel.textAlignment = .center
        statusLabel.font = UIFont.systemFont(ofSize: 16)
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)
        
        // Close button
        closeButton = UIButton(type: .system)
        closeButton.setTitle("Close", for: .normal)
        closeButton.setTitleColor(.white, for: .normal)
        closeButton.backgroundColor = UIColor.systemRed.withAlphaComponent(0.7)
        closeButton.layer.cornerRadius = 8
        closeButton.titleLabel?.font = UIFont.systemFont(ofSize: 18, weight: .semibold)
        closeButton.translatesAutoresizingMaskIntoConstraints = false
        closeButton.addTarget(self, action: #selector(closeTapped), for: .touchUpInside)
        view.addSubview(closeButton)
        
        // Setup constraints
        NSLayoutConstraint.activate([
            // Player view
            playerViewController.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            playerViewController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            playerViewController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            playerViewController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            // Status label
            statusLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            statusLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            
            // Close button
            closeButton.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            closeButton.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            closeButton.widthAnchor.constraint(equalToConstant: 80),
            closeButton.heightAnchor.constraint(equalToConstant: 40)
        ])
    }
    
    func requestVideo() {
        // Build URL for stream command
        var urlComponents = URLComponents()
        urlComponents.scheme = "http"
        urlComponents.host = serverIP
        urlComponents.port = Int(serverPort)
        urlComponents.path = "/mobile_command"
        
        guard let url = urlComponents.url else {
            statusLabel.text = "Invalid server URL"
            return
        }
        
        statusLabel.text = "Requesting video..."
        
        // Create POST request with JSON body
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0
        
        // Create JSON body
        let jsonBody: [String: String] = ["command": "stream"]
        guard let jsonData = try? JSONSerialization.data(withJSONObject: jsonBody) else {
            statusLabel.text = "Failed to create request"
            return
        }
        request.httpBody = jsonData
        
        // Send request
        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else { return }
            
            if let error = error {
                DispatchQueue.main.async {
                    self.statusLabel.text = "Error: \(error.localizedDescription)"
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    self.statusLabel.text = "No data received"
                }
                return
            }
            
            // Parse JSON response
            do {
                guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                    DispatchQueue.main.async {
                        self.statusLabel.text = "Invalid response format"
                    }
                    return
                }
                
                if let status = json["status"] as? String,
                   status == "success",
                   let videoURL = json["video_url"] as? String {
                    // Build full video URL
                    let fullVideoURL = "http://\(self.serverIP):\(self.serverPort)\(videoURL)"
                    DispatchQueue.main.async {
                        self.loadVideo(from: fullVideoURL)
                    }
                } else {
                    let message = json["message"] as? String ?? "Failed to get video URL"
                    DispatchQueue.main.async {
                        self.statusLabel.text = message
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    self.statusLabel.text = "Failed to parse response: \(error.localizedDescription)"
                }
            }
        }
        
        task.resume()
    }
    
    func loadVideo(from urlString: String) {
        guard let url = URL(string: urlString) else {
            statusLabel.text = "Invalid video URL"
            return
        }
        
        statusLabel.text = "Loading video..."
        
        // Create AVPlayer with video URL
        player = AVPlayer(url: url)
        playerViewController.player = player
        
        // Observe player status
        player?.addObserver(self, forKeyPath: "status", options: [.new], context: nil)
        
        // Start playing
        player?.play()
    }
    
    override func observeValue(forKeyPath keyPath: String?, of object: Any?, change: [NSKeyValueChangeKey : Any]?, context: UnsafeMutableRawPointer?) {
        if keyPath == "status" {
            DispatchQueue.main.async {
                if self.player?.status == .readyToPlay {
                    self.statusLabel.text = "Playing..."
                    // Hide status label after 2 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                        UIView.animate(withDuration: 0.3) {
                            self.statusLabel.alpha = 0
                        }
                    }
                } else if self.player?.status == .failed {
                    self.statusLabel.text = "Failed to load video"
                    self.statusLabel.alpha = 1
                }
            }
        }
    }
    
    @objc func closeTapped() {
        player?.pause()
        player?.removeObserver(self, forKeyPath: "status")
        dismiss(animated: true)
    }
}

