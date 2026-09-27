from frame_sampler import FrameSampler


def test_sampler_every_5_frames():
    sampler = FrameSampler(sample_every=5)

    assert sampler.should_process(5)
    assert sampler.should_process(10)
    assert sampler.should_process(15)

    assert not sampler.should_process(1)
    assert not sampler.should_process(6)
    assert not sampler.should_process(9)


if __name__ == "__main__":
    test_sampler_every_5_frames()
    print("All FrameSampler tests passed!")