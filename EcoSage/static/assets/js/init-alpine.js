function data() {
  function getThemeFromLocalStorage() {
    // if user already changed the theme, use it
    if (window.localStorage.getItem('dark')) {
      return JSON.parse(window.localStorage.getItem('dark'))
    }

    // else return their preferences
    return (
      !!window.matchMedia &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
    )
  }

  function setThemeToLocalStorage(value) {
    window.localStorage.setItem('dark', value)
  }

  return {
    dark: getThemeFromLocalStorage(),
    toggleTheme() {
      this.dark = !this.dark
      setThemeToLocalStorage(this.dark)
    },
    isSideMenuOpen: false,
    toggleSideMenu() {
      this.isSideMenuOpen = !this.isSideMenuOpen
    },
    closeSideMenu() {
      this.isSideMenuOpen = false
    },
    isNotificationsMenuOpen: false,
    toggleNotificationsMenu() {
      this.isNotificationsMenuOpen = !this.isNotificationsMenuOpen
    },
    closeNotificationsMenu() {
      this.isNotificationsMenuOpen = false
    },
    isProfileMenuOpen: false,
    toggleProfileMenu() {
      this.isProfileMenuOpen = !this.isProfileMenuOpen
    },
    closeProfileMenu() {
      this.isProfileMenuOpen = false
    },
    isPagesMenuOpen: false,
    togglePagesMenu() {
      this.isPagesMenuOpen = !this.isPagesMenuOpen
    },
  }
  
}

    // Get the modal elements
 var budgetModal = document.getElementById("budgetModal");

// Get the button that opens the modals
var budgetButton = document.getElementById("budgetButton");

// Get the <span> element that closes the modals
var budgetClose = budgetModal.getElementsByClassName("close")[0];

// When the user clicks the button, open the respective modal
budgetButton.onclick = function() {
 budgetModal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
budgetClose.onclick = function() {
 budgetModal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
 if (event.target == budgetModal) {
     budgetModal.style.display = "none";
 }
}

