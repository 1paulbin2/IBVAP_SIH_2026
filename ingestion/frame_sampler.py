class FrameSampler:

    def __init__(self, sample_every=5):
        self.sample_every = sample_every

    def should_process(self, frame_number):
        return frame_number % self.sample_every == 0


if __name__ == "__main__":
    sampler = FrameSampler(sample_every=5)

    for frame_number in range(1, 16):
        if sampler.should_process(frame_number):
            print(f"Processing frame: {frame_number}")