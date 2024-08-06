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
    game = {
      prompt = <<EOF
      Create an engaging and addictive game concept that can be played in about one minute. 
      Game can end due to time limitation or because an error was made.

      The score and best score should be displayed.
      At the end of the game, don't ask the player its nickname. 
      Provide clear instructions on how to play the game at the top of the game. 
      If there are time limit, display the remaining time.

      Code should be in one html file. 

      Make sure all components of the game are visible and respond correctly to the controls. 
      Game should be fully playable, I want to be able to copy paste as is on my website. 
      Ensure the game state is reset properly when the player opts for a rematch

      Make it original and avoid games that require to type words. 
      The game should be simple to understand and easy to play, encouraging players to retry to beat their high scores.
      Players should use either the mouse to click or the keyboard to control the game or a character.

      NO BUG ALLOWED
      EOF
    }
    data = {
      prompt = <<EOF
      Create an article for Data analysis or data science or data engineering. 
      Find a topic/ a technology that is specific and develop it. 
      Article should rely on concrete examples and codes snippets if applicable.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    product = {
      prompt = <<EOF
      Create a Product Manager article article. 
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    management = {
      prompt = <<EOF
      Create an article about management
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    dev = {
      prompt = <<EOF
      Create an article for developers. 
      Find a topic/ a technology that is specific and develop it. 
      Article should rely on concrete examples and codes snippets if applicable.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    startup = {
      prompt = <<EOF
      Create an article for startup entrepreneur. 
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    sales = {
      prompt = <<EOF
      Create an article about sales. 
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    marketing = {
      prompt = <<EOF
      Create an article about marketing. 
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
    design = {
      prompt = <<EOF
      Create an article about digital design. 
      Find a topic/ a method that is specific and develop it. 
      Article should rely on concrete examples.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file 
      EOF
    }
  }
}
