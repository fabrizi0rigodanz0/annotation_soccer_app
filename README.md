# Soccer Video Annotation Tool

A comprehensive application for annotating soccer videos with custom labels, timestamps, and team assignments. This tool allows detailed analysis of soccer matches by creating time-stamped annotations that can be easily reviewed and exported.

## Features

- **Smooth Video Playback**: Efficient video processing for smooth playback of MP4 videos
- **Time-Based Annotations**: Create precise annotations at specific points in the video
- **Soccer-Specific Labels**: Pre-configured with soccer-specific annotation labels
- **Team Assignment**: Assign annotations to home or away teams
- **Intuitive Navigation**: Easy timeline navigation with annotation markers
- **Keyboard Shortcuts**: Spacebar to pause and annotate, and more
- **JSON Export**: All annotations saved in structured JSON format
- **Easy Installation**: Simple setup with minimal dependencies

## Installation

### Prerequisites

- Python 3.7 or higher
- PyQt5
- OpenCV for Python

### Steps

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/soccer-video-annotator.git
   cd soccer-video-annotator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage

### Opening a Video

1. Click the "Open Video" button or use Ctrl+O (Cmd+O on macOS)
2. Navigate to and select your MP4 soccer video file
3. The video will load and display in the main window

### Playback Controls

- **Play/Pause**: Click the play/pause button or press the spacebar
- **Frame Navigation**: Use the step forward/backward buttons for frame-by-frame analysis
- **Timeline**: Click anywhere on the timeline to jump to that position
- **Speed Control**: Adjust playback speed using the speed dropdown (0.25x to 2.0x)

### Creating Annotations

1. Navigate to the desired position in the video
2. Press the spacebar to pause the video and open the annotation panel
3. Select a label from the dropdown (GOAL, CORNER, FREE KICK, etc.)
4. Choose the team (home or away)
5. Click "Save Annotation" to add the annotation

### Managing Annotations

- All annotations appear in the timeline as colored markers
- The annotation table shows details for all annotations
- Double-click an annotation to jump to that position in the video
- Right-click an annotation for additional options (jump to position, remove)

### Annotation Labels

The following soccer-specific annotation labels are available:

- GOAL
- CORNER
- FREE KICK
- BALL RECOVERY AND COUNTER ATTACK
- BUILD-UP PLAY
- POSITIONAL ATTACK
- SWITCHING PLAY
- NO HIGHLIGHT

### Annotation Format

Annotations are saved in a JSON file with the following structure:

```json
{
  "annotations": [
    {
      "gameTime": "1 - 00:01",
      "label": "PASS",
      "position": "1080",
      "team": "away",
      "visibility": "visible"
    }
  ]
}
```

The annotation file is automatically saved in the same directory as the video file with "_Labels.json" appended to the video filename.

## Keyboard Shortcuts

- **Spacebar**: Toggle play/pause and open annotation panel
- **Ctrl+O**: Open video file
- **Ctrl+Q**: Exit application
- **Right Arrow**: Step forward one frame
- **Left Arrow**: Step backward one frame

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **RAM**: 8GB or more recommended for smooth playback
- **Processor**: Modern multi-core processor recommended
- **Graphics**: Basic graphics capabilities for UI rendering
- **Storage**: Depends on video file sizes

## Troubleshooting

### Video Playback Issues

- Ensure your video is in MP4 format
- Try reducing the playback resolution if performance is slow
- Check that OpenCV is properly installed

### Performance Optimization

- Close other resource-intensive applications
- Use lower playback speeds for detailed analysis
- Consider preprocessing very large videos into smaller segments

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV for video processing capabilities
- PyQt5 for the user interface framework
- All contributors to the project

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.