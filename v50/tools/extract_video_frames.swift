import AppKit
import AVFoundation
import Foundation

guard CommandLine.arguments.count >= 3 else {
    FileHandle.standardError.write(Data("usage: extract_video_frames.swift VIDEO OUTPUT_DIR [FPS]\n".utf8))
    exit(2)
}

let videoURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
let fps = CommandLine.arguments.count >= 4 ? max(1, Double(CommandLine.arguments[3]) ?? 15) : 15
try FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)

let asset = AVURLAsset(url: videoURL)
let duration = CMTimeGetSeconds(asset.duration)
guard duration.isFinite, duration > 0 else {
    FileHandle.standardError.write(Data("video duration is unavailable\n".utf8))
    exit(3)
}

let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero

let frameCount = max(2, Int(floor(duration * fps)))
for index in 0..<frameCount {
    let seconds = min(duration - 0.001, Double(index) / fps)
    let image = try generator.copyCGImage(at: CMTime(seconds: seconds, preferredTimescale: 600), actualTime: nil)
    let representation = NSBitmapImageRep(cgImage: image)
    guard let data = representation.representation(using: .png, properties: [:]) else {
        throw NSError(domain: "DeepBazi.VideoFrames", code: 1, userInfo: [NSLocalizedDescriptionKey: "PNG encoding failed"])
    }
    let filename = String(format: "frame_%04d.png", index)
    try data.write(to: outputURL.appendingPathComponent(filename))
}

print("{\"status\":\"extracted\",\"duration\":\(duration),\"fps\":\(fps),\"frames\":\(frameCount)}")
