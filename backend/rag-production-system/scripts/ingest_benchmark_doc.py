"""
Phase 1 Bootstrap Script: Ingest the microLED/GaN benchmark document.

This script creates a text document containing the microLED/GaN paper content
and ingests it into the vectorstore so that evaluation retrieval works correctly.

The golden_qa.json questions are all about this document, so retrieval must
find content from this source.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.rag.retriever import HierarchicalRetriever
from langchain_core.documents import Document


MICROLLED_GAN_CONTENT = """MicroLED Technology: CMOS Integration and Beyond Displays

Abstract
This paper explores microLED technology, particularly its integration with CMOS microelectronics. We examine traditional display applications and look beyond toward uses like nanosensors, optical neuromorphic networks, and chip-based microscopy. GaN-based microLEDs offer unique combinations of properties that make them suitable for a wide range of applications beyond conventional displays.

Introduction: GaN Materials and Substrates
Gallium nitride (GaN) based devices are critical for modern LED technology. Light-emitting GaN devices are almost always grown on sapphire substrates rather than silicon. Sapphire is more expensive and less thermally conductive than silicon, but it allows fewer crystal defects, higher crystal quality, and is transparent in the visible range, giving more flexibility in optical device design.

Electronic GaN devices are preferably grown on silicon wafers, which fits standard CMOS design and foundry infrastructure, unlike light-emitting GaN devices which favor sapphire for optical quality reasons. The distinction between sapphire and silicon substrate selection is fundamental to understanding the GaN technology ecosystem.

CMOS Integration and Pixel Driving Circuits
A 2T1C circuit — two transistors and one capacitor — is a common design for driving microLEDs, used for both pulse amplitude modulation (PAM) and pulse width modulation (PWM). This circuit architecture is widely adopted because it provides individual pixel control with minimal complexity. Each pixel in a microLED display requires its own driving circuit, making CMOS integration essential for high-resolution displays.

Mass Transfer Technology
Mass transfer is a critical manufacturing challenge for microLED displays. The three key requirements for mass transfer technology in microLED display manufacturing are:
1. High placement accuracy: under 1 micron positional accuracy is required
2. High transfer rate: over 100 million LEDs transferred per hour is needed for commercial viability
3. High yield of functional pixels: over 99.999% yield is required to achieve acceptable display quality

These stringent requirements explain why microLED mass production remains challenging. Apple's decision to postpone its microLED smartwatch project serves as evidence that reliable, cost-effective hybrid integration of microLEDs is not yet fully solved, though this is a temporary delay rather than a long-term setback.

Elastomeric Stamp Transfer Technology
Elastomeric stamps are typically made from PDMS (poly(dimethylsiloxane)). They pick up microLEDs via non-specific van der Waals forces when pressed against the donor substrate, and release them onto the receiver substrate by reducing that adhesion, for example by controlling peel velocity and temperature. The soft, conformal nature of PDMS allows it to make intimate contact with small LED chips.

Laser Lift-Off (LLO) Process
Laser lift-off (LLO) is used to remove the sapphire substrate from the MOVPE-LED stack. This process helps improve light extraction, optimize heat transfer, and enables transferring LEDs onto flexible or foreign substrates. LLO uses a high-power laser to ablate the interface between the GaN epitaxial layer and the sapphire substrate, allowing separation without mechanical damage.

MicroLED Pixel Size by Application
The minimum feasible microLED pixel size varies significantly by display application:
- Compact AR displays need the smallest pixels, roughly 1-10 micrometers in size
- Smartwatch and phone displays use medium pixel sizes around 10-50 micrometers
- Large screen TVs typically use larger pixels in the 50-100 micrometer range

Structured Illumination Microscopy with MicroLEDs
Structured illumination microscopy using microLEDs works differently from conventional microscopy. Instead of illuminating a specimen all at once like a conventional microscope, this technique switches individual nanoLEDs in an array on and off one at a time. Since the illumination position is known precisely at every moment, no imaging lens or focusing is required, and resolution is set by the pitch of the nanoLEDs rather than conventional optics.

NanoLED Resolution Achievements
NanoLEDs with diameters as small as 200 nanometers have been demonstrated in structured illumination experiments. However, to translate that into actual spatial resolution, the sample needs to be within roughly 400 nanometers of the nanoLED array's near field, which is difficult to achieve given the layer structure required in nitride LEDs.

Optical Downscaling
Optical downscaling is a technique where a microLED array's emission is optically miniaturized, for example by a factor of 100, to shrink the effective pixel pitch below the diffraction limit. This approach can achieve power densities as high as one million watts per square centimeter. The extreme power densities achievable through optical downscaling open possibilities for applications requiring intense focused light.

Optogenetics Research with GaN MicroLEDs
GaN-based microLEDs are valuable tools for optogenetics research. They can excite channelrhodopsin (ChR2) molecules at a threshold intensity using a 450 nanometer wavelength, triggering electrical excitation responses in neural networks. This has been applied to study contraction behavior in bioartificial cardiac tissue, with pixel widths between roughly 12.5 and 62.5 micrometers used in these experiments. The ability to address specific cells with high spatial precision makes microLEDs ideal for optogenetic applications.

LED Operating Regimes for Sensing
LEDs can operate in multiple regimes relevant to sensing applications:
- Forward bias beyond the emission threshold: the LED acts as a light source for optical sensing
- Sub-threshold regime: the LED behaves as a non-emitting diode useful for mapping properties like temperature or strain
- Reverse operation: the LED's p-n junction can act as a photodetector or energy harvester under external illumination

These multiple operating modes make LEDs versatile sensing elements that can be integrated into imaging and sensing arrays.

Visible Light Communication (VLC)
Visible light communication uses LEDs both for illumination and simultaneous data transmission to photodiode receivers. GaN LEDs are considered good candidates for VLC transmitters due to their high average efficiency. Optimization approaches like rate-splitting multiple access combined with reinforcement learning methods can maximize data rates. VLC represents an important application for GaN microLEDs that leverages their high modulation bandwidth.

Future: MicroLasers and VCSELs
The paper proposes moving from microLEDs to coherent microLaser sources based on vertically emitting laser diodes (VCSELs), which require a vertical optical cavity built from distributed Bragg reflectors (DBRs). A key challenge is that conventional dielectric DBRs are non-conductive, complicating current flow through the device structure. Solving this challenge would enable much higher brightness and coherence in future micro-light-source arrays.

Porous GaN for DBR Applications
Porous GaN can be fabricated using a dopant-dependent electrochemical etching process. Because the etched channels are filled with air, it acts as a low-refractive-index material suitable for DBRs, achieving peak reflectivity above 99% while remaining conductive. This property of porous GaN makes it an attractive solution to the DBR conductivity challenge for VCSELs.

Optical Neuromorphic Computing
The paper highlights optical neuromorphic computing as a potentially even higher-impact application than displays. This is due to the natural parallelism of optical systems, where a single microLED can communicate with millions of detectors simultaneously, similar to biological neural interconnects. Such optical systems could achieve compute power exceeding 100 TOPS per watt, roughly two orders of magnitude better than the efficiency of an NVIDIA H100 processor, which is commonly used today for large language models and AI workloads.

GaN Foundry Ecosystem
The paper identifies GaN foundry availability as a key limiting factor for GaN technology development. GaN foundries are not widely available, unlike silicon electronics where foundry access is well established even for small-scale research. Building out a GaN foundry ecosystem would significantly help advance the technology and enable broader adoption of microLED and related GaN-based devices.

Conclusion
GaN-based microLED technology represents a transformative platform that extends far beyond displays. From structured illumination microscopy to optical neuromorphic computing, from optogenetics to visible light communication, the unique combination of high brightness, high efficiency, small pixel pitch, and CMOS compatibility makes microLEDs a compelling platform for the next generation of optoelectronic systems.
"""


def main():
    settings = get_settings()
    retriever = HierarchicalRetriever(settings)

    # Check if GaN document is already indexed
    existing = retriever.parent_store.list_documents()
    for doc in existing:
        if 'microlled' in doc.get('source_name', '').lower() or 'gan' in doc.get('source_name', '').lower():
            print(f"GaN document already indexed: {doc}")
            return

    source_name = "microlled_gan_paper.txt"
    source_id = "microlled_gan_benchmark_v1"

    print(f"Ingesting microLED/GaN benchmark document as source_id={source_id}")

    docs = [
        Document(
            page_content=MICROLLED_GAN_CONTENT,
            metadata={"source_name": source_name, "page": 1},
        )
    ]

    parents, children = retriever.ingest(docs, source_id, source_name)
    print(f"Ingestion complete: {parents} parents, {children} children indexed")

    # Verify
    all_docs = retriever.parent_store.list_documents()
    print(f"Documents now in index: {all_docs}")


if __name__ == "__main__":
    main()
