variable "region" {
  description = "Region of AWS VPC"
  type        = string
}

variable "openai_token" {
  description = "OpenAI token"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Name of the domain (ex: example.com)"
  type        = string
}

variable "contents" {
  type = map(object({
    prompt = string
  }))
  default = {
    games = {
      prompt = <<EOF
      Create an engaging and addictive game concept that can be played in about one minute. 
      Game can end due to time limitation or because an error was made.

      The score and best score should be displayed.
      At the end of the game, don't ask the player its nickname. 
      Provide clear instructions on how to play the game. 
      If there are time limit, display the remaining time.

      Code should be in one html file. 

      Make sure all components of the game are visible and respond correctly to the controls. 
      Game should be fully playable, I don't want to have to update code to make it work. 
      Ensure the game state is reset properly when the player opts for a rematch

      Make it original and avoid games that require to type words. 
      The game should be simple to understand and easy to play, encouraging players to retry to beat their high scores.
      Players should use either the mouse to click or the keyboard to control the game or a character.
      EOF
    }
    dataeng = {
      prompt = <<EOF
      Create a DataEngineering newsletter content in html. 
      EOF
    }
  }
}
