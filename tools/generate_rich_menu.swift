import AppKit
import Foundation

let outputPath = CommandLine.arguments.count > 1
    ? CommandLine.arguments[1]
    : "assets/line-rich-menu.png"

let width = 2500
let height = 843
let panelWidth = width / 3

struct Panel {
    let background: NSColor
    let accent: NSColor
    let title: String
    let subtitle: String
    let symbol: String
}

let panels = [
    Panel(
        background: NSColor(calibratedRed: 0.965, green: 0.986, blue: 0.969, alpha: 1),
        accent: NSColor(calibratedRed: 0.176, green: 0.435, blue: 0.361, alpha: 1),
        title: "選購顏料",
        subtitle: "$120 / 15克",
        symbol: "色"
    ),
    Panel(
        background: NSColor(calibratedRed: 1.000, green: 0.988, blue: 0.965, alpha: 1),
        accent: NSColor(calibratedRed: 0.792, green: 0.361, blue: 0.220, alpha: 1),
        title: "聯絡客服",
        subtitle: "問題與訂單",
        symbol: "聊"
    ),
    Panel(
        background: NSColor(calibratedRed: 0.957, green: 0.941, blue: 0.898, alpha: 1),
        accent: NSColor(calibratedRed: 0.259, green: 0.435, blue: 0.624, alpha: 1),
        title: "付款說明",
        subtitle: "付款與配送",
        symbol: "付"
    ),
]

func paragraph(_ alignment: NSTextAlignment) -> NSMutableParagraphStyle {
    let style = NSMutableParagraphStyle()
    style.alignment = alignment
    return style
}

func drawCentered(_ text: String, size: CGFloat, weight: NSFont.Weight, color: NSColor, rect: NSRect) {
    let font = NSFont.systemFont(ofSize: size, weight: weight)
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: color,
        .paragraphStyle: paragraph(.center),
    ]
    text.draw(in: rect, withAttributes: attributes)
}

func drawRoundedRect(_ rect: NSRect, radius: CGFloat, color: NSColor) {
    color.setFill()
    NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius).fill()
}

func drawPanel(index: Int, panel: Panel) {
    let x = index * panelWidth
    let rect = NSRect(x: x, y: 0, width: panelWidth, height: height)
    panel.background.setFill()
    rect.fill()

    drawRoundedRect(
        NSRect(x: x + 28, y: 28, width: panelWidth - 56, height: height - 56),
        radius: 0,
        color: panel.accent
    )
    drawRoundedRect(
        NSRect(x: x + 50, y: 50, width: panelWidth - 100, height: height - 100),
        radius: 0,
        color: panel.background
    )

    let badgeSize: CGFloat = 168
    let badge = NSRect(
        x: CGFloat(x) + CGFloat(panelWidth) / 2 - badgeSize / 2,
        y: 166,
        width: badgeSize,
        height: badgeSize
    )
    drawRoundedRect(badge, radius: 34, color: panel.accent)
    drawCentered(panel.symbol, size: 82, weight: .bold, color: .white, rect: NSRect(x: badge.minX, y: badge.minY + 28, width: badge.width, height: 110))

    drawCentered(
        panel.title,
        size: 78,
        weight: .bold,
        color: panel.accent,
        rect: NSRect(x: x + 86, y: 382, width: panelWidth - 172, height: 105)
    )
    drawCentered(
        panel.subtitle,
        size: 42,
        weight: .medium,
        color: NSColor(calibratedWhite: 0.24, alpha: 1),
        rect: NSRect(x: x + 86, y: 512, width: panelWidth - 172, height: 72)
    )
}

let image = NSImage(size: NSSize(width: width, height: height))
image.lockFocus()
NSGraphicsContext.current?.imageInterpolation = .high
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()

for (index, panel) in panels.enumerated() {
    drawPanel(index: index, panel: panel)
}

image.unlockFocus()

guard
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let png = bitmap.representation(using: .png, properties: [:])
else {
    fatalError("Could not render rich menu PNG")
}

try FileManager.default.createDirectory(
    at: URL(fileURLWithPath: outputPath).deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try png.write(to: URL(fileURLWithPath: outputPath))
print(outputPath)
