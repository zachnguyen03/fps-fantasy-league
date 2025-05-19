# [CS:GO Autistic Simulator](https://github.com/zachnguyen03/vct_simulator)

by anhster (in development stage)

## :electron: Why? :electron:
I'm a diehard Esports fan, especially Valorant esports, but the number of matches in a VCT season is diabolical. I'm also autistic, and I hate playing the game. Solution? Making my own fantasy league

## :tada: Introduction :tada:
This is a simple UI for an FPS fantasy league I'm hosting. I love working with data, so I'm using this fantasy league to get into data analytics. We can pretty much customize our own players, metrics, evaluation systems based on our preferences. In my case, I gathered some CS:GO and Valorant pro players, made a custom botprofile.db for CS:GO with custom skill levels for each player, and do matchmaking for 10 bots (yes, I enjoy watching 10 computer-controlled characters play a competitive game of CS:GO). And why CS:GO and not CS2 or Valorant? Because you can actually customize the bots in CS:GO, while CS2 bots are ass and Valorant doesn't even have one

## :hammer_and_wrench: Installation :hammer_and_wrench:

Requirements

The following installation suppose `python=3.9` `gradio` 

- Clone the repository

  ```
  git clone https://github.com/zachnguyen03/vct_simulator.git
  cd vct_simulator
  ```

- Environment Installation
  ```
  conda create -n vct python=3.9
  conda activate vct
  pip install gradio
  ```

- Initialize the UI
  ```
  python app.py
  ```

- User interface preview ![demo](./assets/demo.png)

## :nut_and_bolt: Inference :nut_and_bolt:
- [x] App UI
- [x] Create live game + update scoreboard
- [x] ELO system
- [x] Save match history
- [x] Enhanced ELO system with performance-driven scores
- [ ] OCR integration for automatic scoreboard logging using uploaded screenshot 
- [x] Statistical plots
