import aspose.slides as slides
import aspose.pydrawing as drawing
import os

def preview_pptx(pptx_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    with slides.Presentation(pptx_path) as pres:
        for i, slide in enumerate(pres.slides):
            # 修正方法名为 get_image
            image = slide.get_image(1.0, 1.0)
            output_path = os.path.join(output_folder, f"slide_{i+1:02d}.png")
            image.save(output_path, drawing.imaging.ImageFormat.png)
            print(f"Slide {i+1} saved to {output_path}")

if __name__ == "__main__":
    PPT_PATH = "/basic/homework/mp4_to_ppt/24节气_v3.pptx"
    OUT_DIR = "/basic/homework/mp4_to_ppt/previews"
    preview_pptx(PPT_PATH, OUT_DIR)
